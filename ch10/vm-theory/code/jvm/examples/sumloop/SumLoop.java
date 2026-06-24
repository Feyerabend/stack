// A counted loop: 'for (int i = 1; i <= 10; i++)'. The i++ compiles to the iinc
// instruction, and the loop condition to if_icmpgt + goto.
public class SumLoop {
    public static void main(String[] args) {
        int sum = 0;
        for (int i = 1; i <= 10; i++) {
            sum = sum + i;
        }
        System.out.print("sum 1..10 = ");
        System.out.println(sum);
    }
}
