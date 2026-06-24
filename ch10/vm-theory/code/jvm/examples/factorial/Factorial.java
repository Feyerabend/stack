// Recursion: a static method that calls itself with invokestatic. Each call runs
// in its own sub-interpreter with its own locals and operand stack, so the
// recursion depth lives on Python's call stack.
public class Factorial {
    static int fact(int n) {
        if (n <= 1) {
            return 1;
        }
        return n * fact(n - 1);
    }

    public static void main(String[] args) {
        System.out.print("5! = ");
        System.out.println(fact(5));
    }
}
