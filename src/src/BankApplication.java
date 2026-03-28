import Bank.Bank;

public class BankApplication extends Application {
    private Bank bank;

    public BankApplication(Bank bank) {
        this.bank = bank;
    }

    @Override
    public void init() {
        // Initialize the bank application
    }

    @Override
    public void idle() {
        // Handle idle state of the bank application
    }

    public void createAccount() {
        // Create a new account in the bank
    }

    public void deposit() {
        // Deposit money into an account
    }

    public void withdraw() {
        // Withdraw money from an account
    }

    public void transfer() {
        // Transfer money between accounts
    }

    public void checkBalance() {
        // Check the balance of an account
    }

    public void closeAccount() {
        // Close an existing account
    }
}
