import tkinter as tk
from PIL import Image, ImageTk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from datetime import datetime
from pymongo import MongoClient

class ExpenseTrackerGUI: 
    def __init__(self, master):
        self.master = master
        self.master.title("Expense Tracker")
        self.master.configure(bg='lightgreen')

        self.monthly_salary = 3000
        self.tracker = ExpenseTracker(self.monthly_salary, self.notify_budget)
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['expense_tracker']
        self.expense_collection = self.db['expenses']
        self.expense_collection = self.db['monthly_budgets']
        self.expense_collection = self.db['monthly_salary']
     
        self.create_widgets()

    def create_widgets(self):
        # Buttons
        self.add_expense_button = tk.Button(self.master, text="Add Expense", command=self.add_expense)
        self.add_expense_button.pack(pady=10)

        self.view_balance_button = tk.Button(self.master, text="View Balance", command=self.view_balance)
        self.view_balance_button.pack(pady=10)

        self.view_expenses_button = tk.Button(self.master, text="View Expenses", command=self.view_expenses)
        self.view_expenses_button.pack(pady=10)

        self.view_each_expense_button = tk.Button(self.master, text="View Each Expense", command=self.view_each_expense)
        self.view_each_expense_button.pack(pady=10)

        self.analyze_subcategory_button = tk.Button(self.master, text="Analyze Subcategory", command=self.analyze_subcategory)
        self.analyze_subcategory_button.pack(pady=10)  # New button added


        self.set_budget_button = tk.Button(self.master, text="Set Monthly Budgets", command=self.set_monthly_budgets)
        self.set_budget_button.pack(pady=10)

        self.set_salary_button = tk.Button(self.master, text="Set Monthly Salary", command=self.set_monthly_salary)
        self.set_salary_button.pack(pady=10)

        self.view_budgets_button = tk.Button(self.master, text="View Monthly Budgets", command=self.view_monthly_budgets)
        self.view_budgets_button.pack(pady=10)

        self.view_salary_button = tk.Button(self.master, text="View Monthly Salary", command=self.view_monthly_salary)
        self.view_salary_button.pack(pady=10)

        self.view_budget_balance_button = tk.Button(self.master, text="View Monthly Budget Balance", command=self.view_monthly_budget_balance)
        self.view_budget_balance_button.pack(pady=10)  # New button added

        

        self.exit_button = tk.Button(self.master, text="Exit", command=self.master.destroy)
        self.exit_button.pack(pady=10)

    def add_expense(self):
        expense_window = tk.Toplevel(self.master)

        label_basic_need = tk.Label(expense_window, text="Is the expense for a basic need? (yes/no): ")
        label_basic_need.pack()

        is_basic_need_entry = tk.Entry(expense_window)
        is_basic_need_entry.pack()

        amount_label = tk.Label(expense_window, text="Enter the expense amount: ")
        amount_label.pack()

        amount_entry = tk.Entry(expense_window)
        amount_entry.pack()

        description_label = tk.Label(expense_window, text="Enter a description for the expense: ")
        description_label.pack()

        description_entry = tk.Entry(expense_window)
        description_entry.pack()

        subcategory_label = tk.Label(expense_window, text="Select sub-category of expense: ")
        subcategory_label.pack()

        # Dropdown menu for sub-categories
        sub_categories = ['Food', 'Home', 'Work', 'Education', 'Medical', 'Outfits', 'Other']
        subcategory_var = tk.StringVar(expense_window)
        subcategory_var.set(sub_categories[0])  # Default value
        subcategory_dropdown = tk.OptionMenu(expense_window, subcategory_var, *sub_categories)
        subcategory_dropdown.pack()

        submit_button = tk.Button(expense_window, text="Submit", command=lambda: self.submit_expense(
            is_basic_need_entry.get().lower(), float(amount_entry.get()), description_entry.get(), subcategory_var.get()))
        submit_button.pack()

    def submit_expense(self, is_basic_need, amount, description, subcategory):
        category = 'Basic Needs' if is_basic_need == 'yes' else 'Fun Expenses'
        self.tracker.add_expense(category, amount, description)

        # Get the current date
        current_date = datetime.now().strftime('%d/%m/%Y')

        # Calculate remaining balance
        total_expenses = sum(self.tracker.expenses.values())
        remaining_balance = self.monthly_salary - total_expenses

        # Store the expense data along with the date, category, and subcategory in a CSV file
        with open('expenses.csv', 'a') as file:
            file.write(f"{current_date},{category},{amount},{description},{remaining_balance},{subcategory}\n")

        # Store the expense data in MongoDB
        expense_data = {
            'date': current_date,
            'category': category,
            'amount': amount,
            'description': description,
            'remaining_balance': remaining_balance,
            'subcategory': subcategory
        }
        self.expense_collection.insert_one(expense_data)

    def view_balance(self):
        self.tracker.get_balance()

    def view_expenses(self):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
        labels = ['Basic Needs', 'Fun Expenses']
        sizes = [self.tracker.expenses['Basic Needs'], self.tracker.expenses['Fun Expenses']]
        ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#ff9999', '#66b3ff'])
        ax1.axis('equal')
        ax1.set_title('Expense Distribution')

        data = {'Category': ['Basic Needs', 'Fun Expenses'],
                'Amount Spent': [self.tracker.expenses['Basic Needs'], self.tracker.expenses['Fun Expenses']]}
        df = pd.DataFrame(data)
        table = ax2.table(cellText=df.values, colLabels=df.columns, cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.2)
        ax2.axis('off')

        plt.show()

    def view_each_expense(self):
        # Get the selected date
        selected_date = self.select_date()
        if selected_date is None:
            return

        # Read data from CSV
        df = pd.read_csv('expenses.csv')

        # Filter data for the selected date
        expenses_on_date = df[df['date'] == selected_date]

        # Generate separate pie charts for basic expenses and fun expenses
        self.generate_pie_chart(expenses_on_date, 'Basic Needs')
        self.generate_pie_chart(expenses_on_date, 'Fun Expenses')

    def select_date(self):
        # Open simple dialog to select date
        selected_date = tk.simpledialog.askstring("Select Date", "Enter date (DD/MM/YYYY):")
        try:
            #  date format
            datetime.strptime(selected_date, '%d/%m/%Y')
            return selected_date
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Please enter date in DD/MM/YYYY format.")
            return None

    def generate_pie_chart(self, df, category):
    # Filter data for the given category
       category_df = df[df['category'] == category]

    # Calculate total amount for the category
       total_amount = category_df['amount'].sum()

    # Create labels and percentages for each description
       labels = category_df['description']
       percentages = category_df['amount'] / total_amount * 100

    # Plot pie chart
       plt.figure()
       plt.pie(percentages, labels=labels, autopct=lambda pct: '{:.1f}%'.format(pct))
       plt.title(f'{category} Expenses on {df.iloc[0]["date"]}')
       plt.axis('equal')
       plt.show(block=True)

    def analyze_subcategory(self):
        # Read data from CSV
        df = pd.read_csv('expenses.csv')

        # Group by subcategory and calculate total expenses
        subcategory_expenses = df.groupby('subcategory')['amount'].sum()

        # Plot bar graph
        subcategory_expenses.plot(kind='bar', color='skyblue')
        plt.title('Expense Analysis by Subcategory')
        plt.xlabel('Subcategory')
        plt.ylabel('Total Expense')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()   


    def set_monthly_budgets(self):
        budget_window = tk.Toplevel(self.master)

        label_basic_needs = tk.Label(budget_window, text="Set Monthly Budget for Basic Needs:")
        label_basic_needs.pack()

        basic_needs_budget_entry = tk.Entry(budget_window)
        basic_needs_budget_entry.pack()

        label_fun_expenses = tk.Label(budget_window, text="Set Monthly Budget for Fun Expenses:")
        label_fun_expenses.pack()

        fun_expenses_budget_entry = tk.Entry(budget_window)
        fun_expenses_budget_entry.pack()

        submit_button = tk.Button(budget_window, text="Submit", command=lambda: self.submit_budget(
            float(basic_needs_budget_entry.get()), float(fun_expenses_budget_entry.get())))
        submit_button.pack()

    def submit_budget(self, basic_needs_budget, fun_expenses_budget):
        self.tracker.set_monthly_budget('Basic Needs', basic_needs_budget)
        self.tracker.set_monthly_budget('Fun Expenses', fun_expenses_budget)
        messagebox.showinfo("Budget Set", "Monthly budgets updated successfully.")

        # expense_data = {
        #     # 'category': category,
        #     # 'amount': amount,
        #     # 'description': description
        #     'basic_budget' : basic_needs_budget,
        #      'fun_budget'   :fun_expenses_budget
        # }
        # self.expense_collection.insert_one(expense_data)
    

    def notify_budget(self, category, remaining_budget):
        messagebox.showwarning("Budget Notification", f"You are close to exceeding the monthly budget for {category}!\nRemaining Budget: {remaining_budget}")

    def set_monthly_salary(self):
        salary_window = tk.Toplevel(self.master)
        salary_window.title("Set Monthly Salary")

        label_salary = tk.Label(salary_window, text="Enter Monthly Salary:")
        label_salary.pack()

        salary_entry = tk.Entry(salary_window)
        salary_entry.pack()

        submit_button = tk.Button(salary_window, text="Submit", command=lambda: self.submit_salary(salary_entry.get()))
        submit_button.pack()

    def submit_salary(self, salary):
        try:
            self.monthly_salary = float(salary)
            self.tracker.salary = self.monthly_salary  # Update the salary in the ExpenseTracker instance
            messagebox.showinfo("Salary Set", f"Monthly salary set to {self.monthly_salary}")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid salary (numeric value)")

    #################   LOADS AND SAVES DATA  
    def view_monthly_budgets(self):
        messagebox.showinfo("Monthly Budgets", f"Basic Needs Budget: {self.tracker.monthly_budgets['Basic Needs']}\nFun Expenses Budget: {self.tracker.monthly_budgets['Fun Expenses']}")

    def view_monthly_salary(self):
        messagebox.showinfo("Monthly Salary", f"Monthly Salary: {self.tracker.salary}") 

    def view_monthly_budget_balance(self):
        total_basic_budget = self.tracker.monthly_budgets['Basic Needs']
        total_fun_budget = self.tracker.monthly_budgets['Fun Expenses']
        total_basic_expenses = self.tracker.expenses['Basic Needs']
        total_fun_expenses = self.tracker.expenses['Fun Expenses']
        remaining_basic_budget = total_basic_budget - total_basic_expenses
        remaining_fun_budget = total_fun_budget - total_fun_expenses
        messagebox.showinfo("Monthly Budget Balance", f"Remaining Basic Needs Budget: {remaining_basic_budget}\nRemaining Fun Expenses Budget: {remaining_fun_budget}")
        
                         

           
    

class ExpenseTracker:
    def __init__(self, salary, notify_callback):
        self.salary = salary
        self.expenses = {'Basic Needs': 0, 'Fun Expenses': 0}
        self.each_expense_details = {'Basic Needs': [], 'Fun Expenses': []}
        self.monthly_budgets = {'Basic Needs': 0, 'Fun Expenses': 0}
        self.notify_callback = notify_callback


    #  def __init__(self, salary, notify_callback):
    #     self.salary = salary
    #     self.expenses = {'Basic Needs': 0, 'Fun Expenses': 0}
    #     self.each_expense_details = {'Basic Needs': [], 'Fun Expenses': []}
    #     self.monthly_budgets = {'Basic Needs': 0, 'Fun Expenses': 0}
    #     self.notify_callback = notify_callback    
        

    def add_expense(self, category, amount, description):
        self.expenses[category] += amount
        self.each_expense_details[category].append({'Amount': amount, 'Description': description})
        messagebox.showinfo("Expense Added", f"Expense of ${amount} added for {category}: {description}")
        self.check_budget(category)

    def check_budget(self, category):
        total_expenses = self.expenses[category]
        budget = self.monthly_budgets[category]
        remaining_budget = budget - total_expenses

        if remaining_budget <= 0:
            self.notify_callback(category, remaining_budget)

    def get_balance(self):
        total_expenses = sum(self.expenses.values())
        balance = self.salary - total_expenses
        messagebox.showinfo("Balance", f"Monthly Salary: {self.salary}\nTotal Expenses: {total_expenses}\nRemaining Balance: {balance}")

    def view_each_expense(self):
        # Create a table for each expense category
        for category, expenses in self.each_expense_details.items():
            if expenses:
                data = {'Amount': [expense['Amount'] for expense in expenses],
                        'Description': [expense['Description'] for expense in expenses]}

                # Create pandas DataFrame
                df = pd.DataFrame(data)

                # Display the table using a messagebox
                messagebox.showinfo(f"{category} Expenses", df.to_string(index=False))

    def set_monthly_budget(self, category, budget):
        self.monthly_budgets[category] = budget

        # Automatically check the budget when setting a new budget
        self.check_budget(category)

def main():
    root = tk.Tk()
    app = ExpenseTrackerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()            

















# import tkinter as tk
# from tkinter import messagebox
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# import pandas as pd

# class ExpenseTrackerGUI:
#     def __init__(self, master):
#         self.master = master
#         self.master.title("Expense Tracker")
#         self.master.configure(bg='lightblue')

#         self.monthly_salary = 3000
#         self.tracker = ExpenseTracker(self.monthly_salary, self.notify_budget)
        
#         self.create_widgets()

#     def create_widgets(self):
#         # Buttons
#         self.add_expense_button = tk.Button(self.master, text="Add Expense", command=self.add_expense)
#         self.add_expense_button.pack(pady=10)

#         self.view_balance_button = tk.Button(self.master, text="View Balance", command=self.view_balance)
#         self.view_balance_button.pack(pady=10)

#         self.view_expenses_button = tk.Button(self.master, text="View Expenses", command=self.view_expenses)
#         self.view_expenses_button.pack(pady=10)

#         self.view_each_expense_button = tk.Button(self.master, text="View Each Expense", command=self.view_each_expense)
#         self.view_each_expense_button.pack(pady=10)

#         # New button for setting monthly budgets
#         self.set_budget_button = tk.Button(self.master, text="Set Monthly Budgets", command=self.set_monthly_budgets)
#         self.set_budget_button.pack(pady=10)

#         self.exit_button = tk.Button(self.master, text="Exit", command=self.master.destroy)
#         self.exit_button.pack(pady=10)

#     def add_expense(self):
#         expense_window = tk.Toplevel(self.master)

#         label = tk.Label(expense_window, text="Is the expense for a basic need? (yes/no): ")
#         label.pack()

#         is_basic_need_entry = tk.Entry(expense_window)
#         is_basic_need_entry.pack()

#         amount_label = tk.Label(expense_window, text="Enter the expense amount: ")
#         amount_label.pack()

#         amount_entry = tk.Entry(expense_window)
#         amount_entry.pack()

#         description_label = tk.Label(expense_window, text="Enter a description for the expense: ")
#         description_label.pack()

#         description_entry = tk.Entry(expense_window)
#         description_entry.pack()

#         submit_button = tk.Button(expense_window, text="Submit", command=lambda: self.submit_expense(
#             is_basic_need_entry.get().lower(), float(amount_entry.get()), description_entry.get()))
#         submit_button.pack()

#     def submit_expense(self, is_basic_need, amount, description):
#         category = 'Basic Needs' if is_basic_need == 'yes' else 'Fun Expenses'
#         self.tracker.add_expense(category, amount, description)

#     def view_balance(self):
#         self.tracker.get_balance()

#     def view_expenses(self):
#         # Create figure for the pie chart
#         fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

#         # Pie chart
#         labels = ['Basic Needs', 'Fun Expenses']
#         sizes = [self.tracker.expenses['Basic Needs'], self.tracker.expenses['Fun Expenses']]
#         ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#ff9999', '#66b3ff'])
#         ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
#         ax1.set_title('Expense Distribution')

#         # Data for the table
#         data = {'Category': ['Basic Needs', 'Fun Expenses'],
#                 'Amount Spent': [self.tracker.expenses['Basic Needs'], self.tracker.expenses['Fun Expenses']]}

#         # Create pandas DataFrame
#         df = pd.DataFrame(data)

#         # Table
#         table = ax2.table(cellText=df.values, colLabels=df.columns, cellLoc='center', loc='center')
#         table.auto_set_font_size(False)
#         table.set_fontsize(10)
#         table.scale(1.2, 1.2)

#         # Remove axis for the table
#         ax2.axis('off')

#         plt.show()

#     def view_each_expense(self):
#         # Call the view_each_expense method of the ExpenseTracker class
#         self.tracker.view_each_expense()

#     def set_monthly_budgets(self):
#         budget_window = tk.Toplevel(self.master)

#         label_basic_needs = tk.Label(budget_window, text="Set Monthly Budget for Basic Needs:")
#         label_basic_needs.pack()

#         basic_needs_budget_entry = tk.Entry(budget_window)
#         basic_needs_budget_entry.pack()

#         label_fun_expenses = tk.Label(budget_window, text="Set Monthly Budget for Fun Expenses:")
#         label_fun_expenses.pack()

#         fun_expenses_budget_entry = tk.Entry(budget_window)
#         fun_expenses_budget_entry.pack()

#         submit_button = tk.Button(budget_window, text="Submit", command=lambda: self.submit_budget(
#             float(basic_needs_budget_entry.get()), float(fun_expenses_budget_entry.get())))
#         submit_button.pack()

#     def submit_budget(self, basic_needs_budget, fun_expenses_budget):
#         self.tracker.set_monthly_budget('Basic Needs', basic_needs_budget)
#         self.tracker.set_monthly_budget('Fun Expenses', fun_expenses_budget)
#         messagebox.showinfo("Budget Set", "Monthly budgets updated successfully.")

#     def notify_budget(self, category, remaining_budget):
#         messagebox.showwarning("Budget Notification", f"You are close to exceeding the monthly budget for {category}!\nRemaining Budget: ${remaining_budget}")

# class ExpenseTracker:
#     def __init__(self, salary, notify_callback):
#         self.salary = salary
#         self.expenses = {'Basic Needs': 0, 'Fun Expenses': 0}
#         self.each_expense_details = {'Basic Needs': [], 'Fun Expenses': []}
#         self.monthly_budgets = {'Basic Needs': 0, 'Fun Expenses': 0}
#         self.notify_callback = notify_callback

#     def add_expense(self, category, amount, description):
#         self.expenses[category] += amount
#         self.each_expense_details[category].append({'Amount': amount, 'Description': description})
#         messagebox.showinfo("Expense Added", f"Expense of ${amount} added for {category}: {description}")
#         self.check_budget(category)

#     def check_budget(self, category):
#         total_expenses = self.expenses[category]
#         budget = self.monthly_budgets[category]
#         remaining_budget = budget - total_expenses

#         if remaining_budget <= 0:
#             self.notify_callback(category, remaining_budget)

#     def get_balance(self):
#         total_expenses = sum(self.expenses.values())
#         balance = self.salary - total_expenses
#         messagebox.showinfo("Balance", f"Monthly Salary: ${self.salary}\nTotal Expenses: ${total_expenses}\nRemaining Balance: ${balance}")

#     def view_expenses(self):
#         expense_details = "\nExpense Details:"
#         for category, amount in self.expenses.items():
#             expense_details += f"\n{category}: ${amount}"
#         messagebox.showinfo("Expenses", expense_details)

#     def view_each_expense(self):
#         # Create a table for each expense category
#         for category, expenses in self.each_expense_details.items():
#             if expenses:
#                 data = {'Amount': [expense['Amount'] for expense in expenses],
#                         'Description': [expense['Description'] for expense in expenses]}

#                 # Create pandas DataFrame
#                 df = pd.DataFrame(data)

#                 # Display the table using a messagebox
#                 messagebox.showinfo(f"{category} Expenses", df.to_string(index=False))

#     def set_monthly_budget(self, category, budget):
#         self.monthly_budgets[category] = budget

#         # Automatically check the budget when setting a new budget
#         self.check_budget(category)

# def main():
#     root = tk.Tk()
#     app = ExpenseTrackerGUI(root)
#     root.mainloop()

# if __name__ == "__main__":
#     main()
