import subprocess


cpp_code = """
#include <iostream>
using namespace std;
int main() {
    int a = 2, b = 3;
    cout << a + b << endl;
    return 0;
}
"""

with open("input.txt", "r") as f:
    input_data = f.read()

result = subprocess.run([
    "python3", "cpp_judge.py", cpp_code, input_data
], capture_output=True)

print(result.stdout.decode())