# Lab2. Unit_test

First of all, we need a [script (in my case it's bash)](tests/TestTriangles.sh) for the tests to see modules in src directory

I've made [20 tests](tests/test_Triangles.py) for [lab1](src/Triangles.py) and [10 tests](tests/test_Delivery.py) for [lab2](src/Delivery.py)

Result (lab1):
```
saikou@MacBook-Air-Saikou PTPM-VKI % ./tests/TestTriangles.sh

...Error: Cannot convert '' into a number.
Traceback (most recent call last):
  File "/Users/saikou/Developer/PythonTesting/PTPM-VKI/src/Triangles.py", line 14, in convert_float
    result = float(str_conv)
ValueError: could not convert string to float: ''
.Error: Cannot convert 'abc' into a number.
Traceback (most recent call last):
  File "/Users/saikou/Developer/PythonTesting/PTPM-VKI/src/Triangles.py", line 14, in convert_float
    result = float(str_conv)
ValueError: could not convert string to float: 'abc'
............Geometric Rule Violation: Sides [3.0, 4.0, 7.0] cannot form a triangle.
.Geometric Rule Violation: Sides [-3.0, 4.0, 5.0] cannot form a triangle.
.Geometric Rule Violation: Sides [1.0, 1.0, 10.0] cannot form a triangle.
.Geometric Rule Violation: Sides [0, 0, 0] cannot form a triangle.
.
----------------------------------------------------------------------
Ran 20 tests in 0.001s

OK
```

It passed! The errors are because of [`logger.exception`](src/Triangles.py#L18) style of handling the logs in certain places

Now for the lab2

```
saikou@MacBook-Air-Saikou PTPM-VKI % ./tests/TestDelivery.sh

.FF......
======================================================================
FAIL: test_express_delivery_modifier (tests.test_Delivery.TestDeliveryCost.test_express_delivery_modifier)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/saikou/Developer/PythonTesting/PTPM-VKI/tests/test_Delivery.py", line 58, in test_express_delivery_modifier
    self.assertEqual(cost, 7800)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: 2600 != 7800

======================================================================
FAIL: test_express_delivery_zero_days (tests.test_Delivery.TestDeliveryCost.test_express_delivery_zero_days)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/saikou/Developer/PythonTesting/PTPM-VKI/tests/test_Delivery.py", line 63, in test_express_delivery_zero_days
    self.assertEqual(date, "2026-09-04")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: '2026-09-03' != '2026-09-04'
- 2026-09-03
?          ^
+ 2026-09-04
?          ^


----------------------------------------------------------------------
Ran 9 tests in 0.001s

FAILED (failures=2)
```

Uh oh! **2 tests have failed...** Let's break down what happened and how we can fix the original source code

|Failed test | Line | What happened | How to fix |
--- | --- | --- | --- |
test_express_delivery_modifie | [36](src/Delivery.py#L36) | It needs to be 1.5x but in the actual code `if is_express: total_cost *= 0.5` it makes it 0.5x | Change to `if is_express: total_cost *= 1.5`|
test_express_delivery_zero_days | [44](src/Delivery.py#L44) | If it's the express delivery then it's 2x faster, but it doesn't check that the delivery days can go down to 0 `if is_express: days_needed = days_needed // 2` | Change to `if is_express: days_needed = max(1, days_needed // 2)`