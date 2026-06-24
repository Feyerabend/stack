// Euclid's algorithm: a while loop driven by goto + ifeq, using irem for the
// modulo. Shows control flow without an induction variable (no iinc here).
public class Gcd {
    static int gcd(int a, int b) {
        while (b != 0) {
            int t = b;
            b = a % b;
            a = t;
        }
        return a;
    }

    public static void main(String[] args) {
        System.out.print("gcd(48, 36) = ");
        System.out.println(gcd(48, 36));
    }
}
