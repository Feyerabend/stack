// Integer arithmetic: the iadd/isub/imul/idiv/irem instructions, and printing
// an int (which exercises println(I), i.e. the descriptor argument counter).
//
// Note: string concatenation with '+' is deliberately avoided -- modern javac
// compiles it to an invokedynamic call this teaching interpreter does not model.
// We print a label with print(String) and the number with println(int) instead.
public class Arithmetic {
    public static void main(String[] args) {
        int a = 2, b = 3, c = 4;

        System.out.print("(2 + 3) * 4 = ");
        System.out.println((a + b) * c);

        System.out.print("20 / 3 = ");
        System.out.println(20 / 3);

        System.out.print("20 % 3 = ");
        System.out.println(20 % 3);
    }
}
