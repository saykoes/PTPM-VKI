import re
import time
from urllib.parse import urlencode, urlparse
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait

import logging

class EtagiParser:
    BASE_URL = "https://novosibirsk.etagi.com/realty/"

    def __init__(self, headless: bool = True, timeout: int = 15):
        self.timeout = timeout
        options = Options()
        options.page_load_strategy = "eager"
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
        )

        self.driver = webdriver.Edge(options=options)
        self.driver.set_page_load_timeout(30)
        self.driver.implicitly_wait(0) 
        
        self.logger = logging.getLogger(__name__)


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def build_search_url(
        self,
        rooms: list[int] | None = None,
        price_min: int | None = None,
        price_max: int | None = None,
        square_min: int | None = None,
        square_max: int | None = None,
        district_ids: list[int] | None = None,
        street_ids: list[int] | None = None,
        newcomplex_ids: list[int] | None = None,
        floor_min: int | None = None,
        floor_max: int | None = None,
        building_year_min: int | None = None,
        order: str | None = None,
        page: int = 1,
    ) -> str:
        params: list[tuple[str, str | int]] = []

        if rooms:
            seen_rooms = set()
            for room in rooms:
                etagi_room = ">4" if int(room) >= 4 else str(room)
                if etagi_room not in seen_rooms:
                    seen_rooms.add(etagi_room)
                    params.append(("rooms[]", etagi_room))
        if district_ids:
            for d_id in district_ids:
                params.append(("district_id[]", d_id))
        if street_ids:
            for s_id in street_ids:
                params.append(("street_id[]", s_id))
        if newcomplex_ids:
            for nc_id in newcomplex_ids:
                params.append(("newcomplex_id[]", nc_id))

        scalar_filters = {
            "price_min": price_min,
            "price_max": price_max,
            "square_min": int(square_min) if square_min is not None else None,
            "square_max": int(square_max) if square_max is not None else None,
            "floor_min": floor_min,
            "floor_max": floor_max,
            "building_year_min": building_year_min,
            "order": order,
            "map_mode": 0,
        }
        for key, value in scalar_filters.items():
            if value is not None:
                params.append((key, value))

        if page > 1:
            params.append(("page", page))

        query_string = urlencode(params, safe="[]")
        return f"{self.BASE_URL}?{query_string}" if query_string else self.BASE_URL

    def parse_raw_card(self, raw_card: dict) -> dict | None:
        try:
            url = None
            object_id = None

            for absolute_url in raw_card.get("links", []):
                parsed_url = urlparse(absolute_url)
                path_parts = [
                    part for part in parsed_url.path.strip("/").split("/")
                    if part
                ]

                if not path_parts:
                    continue

                last_part = path_parts[-1]

                if not last_part.isdigit():
                    continue

                if "realty" not in path_parts and "zastr" not in path_parts:
                    continue

                url = absolute_url
                object_id = last_part
                break

            if object_id is None or url is None:
                return None

            lines = [
                line.strip()
                for line in raw_card.get("text", "").split("\n")
                if line.strip()
            ]

            prices: list[int] = []
            price_per_m2 = None
            area_m2 = None
            floor = None

            for line in lines:
                if "/м2" in line or "/м²" in line:
                    digits = re.sub(r"\D", "", line.split("/")[0])
                    price_per_m2 = int(digits) if digits else None

                elif re.fullmatch(r"[\d\s]+₽?", line):
                    digits = re.sub(r"\D", "", line)
                    if digits and int(digits) > 100_000:
                        prices.append(int(digits))

                elif re.search(r"[\d,\.]+\s*м[2²]", line, re.IGNORECASE):
                    match = re.search(r"([\d,.]+)\s*м[2²]", line, re.IGNORECASE)
                    if match:
                        area_m2 = float(
                            match.group(1).replace(",", ".")
                        )

                elif re.search(r"\d+/\d+\s*эт", line, re.IGNORECASE):
                    floor = line

            price = prices[0] if prices else None
            old_price = prices[1] if len(prices) > 1 else None

            rooms_label = next(
                (
                    line for line in lines
                    if "комн" in line.lower()
                    or "студия" in line.lower()
                ),
                None,
            )

            address = next(
                (
                    line for line in lines
                    if any(
                        marker in line.lower()
                        for marker in (
                            "ул.",
                            "пр-т",
                            "пер.",
                            "р-н",
                            "жк ",
                            "ш.",
                            "новосибирск",
                            "район",
                        )
                    )
                ),
                None,
            )

            return {
                "id": object_id,
                "url": url,
                "title": rooms_label,
                "area_m2": area_m2,
                "floor": floor,
                "price_rub": price,
                "old_price_rub": old_price,
                "price_per_m2_rub": price_per_m2,
                "address": address,
                "images": raw_card.get("images", [])[:3],
                "raw_lines": lines,
            }

        except Exception:
            return None

    def extract_cards_from_dom(self, selector: str) -> list[dict]:
        raw_cards = self.driver.execute_async_script(
            """
            const selector = arguments[0];
            const callback = arguments[arguments.length - 1];

            async function scrollAndCollect() {
                const seen = new Map();
                const step = Math.max(window.innerHeight * 0.7, 500);
                let currentY = 0;
                let stalled = 0;
                let lastSize = 0;

                function harvestVisibleCards() {
                    const cards = document.querySelectorAll(selector);
                    cards.forEach((card, idx) => {
                        const links = Array.from(card.querySelectorAll("a[href]")).map(a => a.href);
                        const key = links[0] || `card_${idx}`;

                        const images = [];
                        // 1. Check standard <img> tags (src, data-src, srcset)
                        card.querySelectorAll("img").forEach(img => {
                            const candidates = [
                                img.currentSrc,
                                img.getAttribute("src"),
                                img.getAttribute("data-src"),
                                img.getAttribute("data-lazy-src"),
                            ];
                            if (img.srcset) {
                                const first = img.srcset.split(",")[0].trim().split(" ")[0];
                                candidates.push(first);
                            }
                            for (const url of candidates) {
                                if (url && url.startsWith("http") && !images.includes(url)) {
                                    images.push(url);
                                }
                            }
                        });

                        // 2. Fallback: check inline background-image styles
                        if (images.length === 0) {
                            card.querySelectorAll("[style*='background-image']").forEach(el => {
                                const match = el.style.backgroundImage.match(/url\\(["']?(https?:[^"')]+)["']?\\)/);
                                if (match && match[1] && !images.includes(match[1])) {
                                    images.push(match[1]);
                                }
                            });
                        }

                        const existing = seen.get(key);
                        // Keep or upgrade entry if we now captured images that weren't loaded earlier
                        if (!existing || (existing.images.length === 0 && images.length > 0)) {
                            seen.set(key, {
                                links: links,
                                text: card.innerText || card.textContent || "",
                                images: images.slice(0, 3),
                            });
                        }
                    });
                }

                // Harvest initial viewport before scrolling
                harvestVisibleCards();

                for (let i = 0; i < 20; i++) {
                    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
                    currentY = Math.min(currentY + step, maxScroll);
                    window.scrollTo(0, currentY);

                    await new Promise(r => setTimeout(r, 150));
                    harvestVisibleCards();

                    if (seen.size === lastSize) {
                        stalled++;
                    } else {
                        stalled = 0;
                    }
                    lastSize = seen.size;

                    if (currentY >= maxScroll - 5 && stalled >= 2) {
                        break;
                    }
                }

                callback(Array.from(seen.values()));
            }

            scrollAndCollect();
            """,
            selector,
        )

        results = []
        for raw_card in raw_cards or []:
            parsed = self.parse_raw_card(raw_card)
            if parsed and parsed["id"]:
                results.append(parsed)
        return results


    def search(self, **filters) -> dict:
        url = self.build_search_url(**filters)
        cards_selector = "#object-list [data-testid='object_card']"

        try:
            self.driver.get(url)
        except TimeoutException:
            self.driver.execute_script("window.stop();")

        self.logger.debug("[TIMING] Initial page load complete") # debug

        current_host = urlparse(self.driver.current_url).hostname or ""

        if not current_host.endswith("etagi.com"):
            try:
                self.driver.get(url)
            except TimeoutException:
                self.driver.execute_script("window.stop();")
        
        wait_start = time.time()  # debug
        wait = WebDriverWait(self.driver, self.timeout)

        try:
            # Ждём появления самих карточек внутри #object-list либо сообщения о пустом поиске
            wait.until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, cards_selector)) > 0
                or "0 предложений" in d.find_element(By.ID, "searchObjectListRoot").text.lower()
                or "нет предложений" in d.find_element(By.ID, "searchObjectListRoot").text.lower()
            )
            self.logger.debug("[TIMING] Cards appeared after %.2fs", time.time() - wait_start) # debug
        except TimeoutException:
            raise RuntimeError(
                f"Cards did not appear in #object-list after {self.timeout}s. "
                f"URL: '{self.driver.current_url}'"
            )

        collected: dict[str, dict] = {}

        max_pages = 5
        filters = {k: v for k, v in filters.items() if k != "page"}

        for page_num in range(1, max_pages + 1):
            # Trigger lazy-loading once if needed, then extract all cards in one JS call
            #self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            extract_start = time.time() # debug
            page_items = self.extract_cards_from_dom(cards_selector)
            
            # sanity check after 1st page
            if page_num == 1 and not page_items and len(self.driver.find_elements(By.CSS_SELECTOR, cards_selector)) > 0:
                raise RuntimeError(
                    "Cards rendered on page 1, but 0 items were parsed. Check parse_raw_card."
                )
            
            for item in page_items:
                collected[item["id"]] = item

            self.logger.debug(
                f"[TIMING] Page {page_num}: extracted {len(page_items)} cards "
                f"in {time.time() - extract_start:.3f}s (total={len(collected)})"
            )  # debug

            if len(collected) >= 100 or page_num >= max_pages:
                break

            next_url = self.build_search_url(page=page_num + 1, **filters)
            nav_start = time.time() # debug
            try:
                self.driver.get(next_url)
            except TimeoutException:
                self.driver.execute_script("window.stop();")

            self.logger.debug(f"[TIMING] Navigation to page {page_num + 1} took {time.time() - nav_start:.2f}s") # debug

            try:
                wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, cards_selector)) > 0)
            except TimeoutException:
                break

        items = list(collected.values())


        return {
            "search_url": url,
            "count": len(items),
            "items": items
        }

    def close(self):
        if self.driver:
            self.driver.quit()
