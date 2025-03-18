def sum_of_squares(n):
    return sum(x**2 for x in range(n+1))

if __name__ == "__main__":
    result = sum_of_squares(50)
    print(f"Computation completed: The sum of squares up to 50 is {result}")
