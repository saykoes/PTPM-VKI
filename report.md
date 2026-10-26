# Lab 3. Integrational tests.

We are going to structurize modules in multiple calsses with different responsibilities

But before that, we need to do a db work

I've created a Triangle data class for easier work
```python
@dataclass
class Triangle:
    """Data model for Triangle"""
    side_a: float
    side_b: float
    side_c: float
    id: Optional[int] = None
```

Now we need an entity to talk to a db and that's going to be `TriangleRepository`

```python
class TriangleRepository:
    """Repository for SQLite database operations"""
    
    # get the filename of a db
    def __init__(self, db_name: str = "triangles.db"):
        self.db_name = db_name

    def init_db(self) -> None:
        """Creates the necessary tables if they do not exist"""
        logger.info("Initializing database...")
        # Using a context manager 'with' automatically closes the connection
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS triangles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    side_a REAL NOT NULL,
                    side_b REAL NOT NULL,
                    side_c REAL NOT NULL,
                    pixel_points TEXT
                )
            """)
            conn.commit()
        logger.debug("Database table initialized successfully")

```

Now that we initialized the db, let's make C and R from CRUD

```python

```

Let's decouple the input and calculation logic into separate files and classes

For input, let's make a dependency injection via strategy

We create the abstract class with method
```python
class InputService(Protocol):
    """Like interface in csharp"""
    def read(self, prompt: str) -> str:
        # Abstract method
        ... 
```

and two services

1. Console 
```python
class ConsoleInputService:
    def read(self, prompt: str) -> str:
        return input(prompt)

```

2. Mock for tests
```python
class MockInputService:
    def __init__(self, return_values: list[str]):
        # Turn list into iterator
        self.outputs = iter(return_values)
        
    def read(self, prompt: str) -> str:
        return next(self.outputs)
```

It's gonna be used as a stub (data placeholder)

