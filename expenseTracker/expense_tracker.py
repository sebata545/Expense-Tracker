import matplotlib
matplotlib.use('Qt5Agg')
import csv
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
from collections import defaultdict
import calendar
import pandas as pd

class ExpenseTracker:
    def __init__(self, data_file="expenses.csv", budget_file="budgets.json"):
        self.data_file = data_file
        self.budget_file = budget_file
        self.expenses = []
        self.categories = [
            "Food", "Transportation", "Housing", "Entertainment", 
            "Utilities", "Healthcare", "Education", "Shopping", "Other"
        ]
        self.category_budgets = {}
        self.load_data()
        self.load_budgets()

    def load_data(self):
        """Load expense data from file"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                reader = csv.DictReader(f)
                self.expenses = list(reader)  
                for expense in self.expenses:
                    expense['amount'] = float(expense['amount'])
                    expense['date'] = datetime.strptime(expense['date'], "%Y-%m-%d %H:%M")

    def save_data(self):
        """Save expense data to file"""
        with open(self.data_file, 'w', newline='') as f:
            fieldnames = ['date', 'description', 'category', 'amount']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for expense in self.expenses:
                temp = expense.copy()
                temp['date'] = temp['date'].strftime("%Y-%m-%d %H:%M")
                writer.writerow(temp)

    def load_budgets(self):
        """Load budget data from file"""
        if os.path.exists(self.budget_file):
            with open(self.budget_file, 'r') as f:
                self.category_budgets = json.load(f)

    def save_budgets(self):
        """Save budget data to file"""
        with open(self.budget_file, 'w') as f:
            json.dump(self.category_budgets, f, indent=2)

    def add_expense(self, description, category, amount):
        """Add a new expense"""
        if category not in self.categories:
            category = "Other"
            
        try:
            amount = float(amount)
        except ValueError:
            print("Invalid amount. Please enter a number.")
            return
            
        expense = {
            'date': datetime.now(),
            'description': description,
            'category': category,
            'amount': amount
        }
        
        self.expenses.append(expense)
        self.save_data()
        print(f"Added expense: ${amount:.2f} for {description}")
        
        self.check_budget_alert(category, amount)

    def view_expenses(self, filter_category=None, month=None, year=None):
        """View expenses with filters"""
        print("\n--- Expenses ---")
        if not self.expenses:
            print("No expenses recorded yet.")
            return
        
        filtered = self.expenses
        
        if filter_category:
            filtered = [e for e in filtered if e['category'] == filter_category]
            
        if month or year:
            filtered = [e for e in filtered 
                       if (not month or e['date'].month == month) 
                       and (not year or e['date'].year == year)]
            
        if not filtered:
            print("No expenses match your filters.")
            return
            
        for i, expense in enumerate(filtered, 1):
            date_str = expense['date'].strftime("%Y-%m-%d")
            print(f"{i}. {date_str} - {expense['description']} ({expense['category']}): ${expense['amount']:.2f}")
        
        total = sum(e['amount'] for e in filtered)
        print(f"\nTotal: ${total:.2f}")


    def get_summary(self, month=None, year=None):
        """Generate expense summary by category with date filters"""
        summary = defaultdict(float)
        total = 0.0
        
        for expense in self.expenses:
            if month and expense['date'].month != month:
                continue
            if year and expense['date'].year != year:
                continue
                
            summary[expense['category']] += expense['amount']
            total += expense['amount']
        
        return summary, total

    def show_summary(self, month=None, year=None):
        """Display expense summary with budget comparison"""
        if not self.expenses:
            print("No expenses to summarize.")
            return
            
        summary, total = self.get_summary(month, year)
        
        date_header = ""
        if month and year:
            date_header = f" for {calendar.month_name[month]} {year}"
        elif year:
            date_header = f" for {year}"

        print(f"\n--- Expense Summary{date_header} ---")
        for category, amount in summary.items():
            budget = self.category_budgets.get(category, 0)
            remaining = budget - amount if budget > 0 else 0
            status = ""
            
            if budget > 0:
                if amount > budget:
                    status = " (OVER BUDGET!)"
                else:
                    status = f" (${remaining:.2f} remaining)"
            
            print(f"{category}: ${amount:.2f}{status}")
        print(f"\nTotal Expenses: ${total:.2f}")

    def plot_expenses(self, month=None, year=None):
        """Create visualizations of expenses"""
        if not self.expenses:
            print("No expenses to visualize.")
            return
            
        summary, total = self.get_summary(month, year)
        
        labels = []
        sizes = []
        colors = plt.cm.tab20.colors  
        
        for i, (category, amount) in enumerate(summary.items()):
            if amount > 0:
                labels.append(category)
                sizes.append(amount)
        

        plt.figure(figsize=(14, 8))
        
        plt.subplot(1, 2, 1)
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', 
                colors=colors[:len(labels)], startangle=140)
        plt.axis('equal')
        plt.title('Expense Distribution')
        
        plt.subplot(1, 2, 2)
        categories = list(summary.keys())
        actuals = [summary[cat] for cat in categories]
        budgets = [self.category_budgets.get(cat, 0) for cat in categories]
        
        x = range(len(categories))
        bar_width = 0.35
        
        plt.bar(x, actuals, width=bar_width, label='Actual', color='skyblue')
        plt.bar([pos + bar_width for pos in x], budgets, width=bar_width, label='Budget', color='lightgreen')
        
        plt.xlabel('Categories')
        plt.ylabel('Amount ($)')
        plt.title('Actual vs Budgeted Spending')
        plt.xticks([pos + bar_width/2 for pos in x], categories, rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        
        plt.savefig('expense_analysis.png')
        print("Saved expense analysis to 'expense_analysis.png'")
        plt.close()  


    def spending_trends(self):
        """Show monthly spending trends"""
        if not self.expenses:
            print("No expenses to analyze trends.")
            return
            
        df = pd.DataFrame(self.expenses)
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])
        df['month_year'] = df['date'].dt.strftime('%Y-%m')
        
        monthly = df.groupby('month_year')['amount'].sum().reset_index()
        
        plt.figure(figsize=(12, 6))
        plt.bar(monthly['month_year'], monthly['amount'], color='royalblue')
        
        if self.category_budgets:
            total_budget = sum(self.category_budgets.values())
            plt.axhline(y=total_budget, color='r', linestyle='-', 
                       label=f'Monthly Budget (${total_budget:.2f})')
            plt.legend()
        
        plt.xlabel('Month')
        plt.ylabel('Total Spending ($)')
        plt.title('Monthly Spending Trends')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        plt.savefig('spending_trends.png')
        print("Saved spending trends to 'spending_trends.png'")
        plt.close()  

    def set_budgets(self):
        """Set budgets for each category"""
        print("\nSet Monthly Budgets:")
        for category in self.categories:
            current = self.category_budgets.get(category, 0)
            budget = input(f"Budget for {category} (current: ${current:.2f}): $")
            try:
                self.category_budgets[category] = float(budget) if budget else 0
            except ValueError:
                print("Invalid input. Budget not changed.")
        
        self.save_budgets()
        print("Budgets updated successfully!")

    def check_budget_alert(self, category, amount):
        """Check if expense exceeds budget and alert"""
        budget = self.category_budgets.get(category, 0)
        if budget <= 0:
            return
            
        now = datetime.now()
        category_total = sum(
            e['amount'] for e in self.expenses 
            if e['category'] == category 
            and e['date'].month == now.month 
            and e['date'].year == now.year
        )
        
        if category_total > budget:
            print("\n" + "!" * 50)
            print(f" BUDGET ALERT: You've exceeded your {category} budget!")
            print(f" Budget: ${budget:.2f} | Spent: ${category_total:.2f}")
            print("!" * 50)

    def monthly_report(self, month=None, year=None):
        """Generate detailed monthly report"""
        if not month or not year:
            now = datetime.now()
            month = month or now.month
            year = year or now.year
            
        month_expenses = [
            e for e in self.expenses 
            if e['date'].month == month and e['date'].year == year
        ]
        
        if not month_expenses:
            print(f"No expenses for {calendar.month_name[month]} {year}")
            return
            
        report = {
            "month": calendar.month_name[month],
            "year": year,
            "total": sum(e['amount'] for e in month_expenses),
            "by_category": defaultdict(float),
            "expenses": []
        }
        
        for e in month_expenses:
            report["by_category"][e['category']] += e['amount']
            report["expenses"].append({
                "date": e['date'].strftime("%Y-%m-%d"),
                "description": e['description'],
                "category": e['category'],
                "amount": e['amount']
            })
        
        report["by_category"] = dict(report["by_category"])
        
        filename = f"expense_report_{year}_{month}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"Monthly report saved to {filename}")
        return report

    def export_to_json(self, filename="expenses.json"):
        """Export expenses to JSON file"""
        export_data = []
        for expense in self.expenses:
            temp = expense.copy()
            temp['date'] = temp['date'].strftime("%Y-%m-%d %H:%M")
            export_data.append(temp)
            
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        print(f"Data exported to {filename}")

    def clear_all_expenses(self):
        """Delete all expenses from the tracker and file"""
        self.expenses = []
        self.save_data()
        print("All expenses have been cleared.")

    def clear_all_budgets(self):
        """Delete all budgets from the tracker and file"""
        self.category_budgets = {}
        self.save_budgets()
        print("All budgets have been cleared.")

    def run(self):
        """Main application loop"""
        while True:
            print("\n=== EXPENSE TRACKER ===")
            print("1. Add Expense")
            print("2. View All Expenses")
            print("3. View Expenses by Category")
            print("4. View Expense Summary")
            print("5. Set Budgets")
            print("6. Show Expense Analysis")
            print("7. Show Spending Trends")
            print("8. Generate Monthly Report")
            print("9. Export Data")
            print("10. Clear All Expenses")
            print("11. Clear All Budgets")
            print("12. Exit")
            
            choice = input("\nEnter your choice: ")
            
            if choice == '1':
                print("\nAdd New Expense")
                description = input("Description: ")
                
                print("\nCategories:")
                for i, category in enumerate(self.categories, 1):
                    print(f"{i}. {category}")
                    
                cat_choice = input("Choose category (1-9): ")
                try:
                    category = self.categories[int(cat_choice)-1]
                except:
                    category = "Other"
                    
                amount = input("Amount: $")
                self.add_expense(description, category, amount)
                
            elif choice == '2':
                self.view_expenses()
                
            elif choice == '3':
                print("\nCategories:")
                for i, category in enumerate(self.categories, 1):
                    print(f"{i}. {category}")
                    
                cat_choice = input("Choose category to view (1-9): ")
                try:
                    category = self.categories[int(cat_choice)-1]
                    self.view_expenses(filter_category=category)
                except:
                    print("Invalid category selection")
                    
            elif choice == '4':
                month = input("Enter month (1-12, leave blank for all): ")
                year = input("Enter year (YYYY, leave blank for all): ")
                try:
                    self.show_summary(
                        month=int(month) if month else None,
                        year=int(year) if year else None
                    )
                except ValueError:
                    print("Invalid month/year format")
                    
            elif choice == '5':
                self.set_budgets()
                
            elif choice == '6':
                month = input("Enter month (1-12, leave blank for all): ")
                year = input("Enter year (YYYY, leave blank for all): ")
                try:
                    self.plot_expenses(
                        month=int(month) if month else None,
                        year=int(year) if year else None
                    )
                except ValueError:
                    print("Invalid month/year format")
                    
            elif choice == '7':
                self.spending_trends()
                
            elif choice == '8':
                month = input("Enter month (1-12): ")
                year = input("Enter year (YYYY): ")
                try:
                    self.monthly_report(month=int(month), year=int(year))
                except ValueError:
                    print("Invalid month/year format")
                    
            elif choice == '9':
                filename = input("Enter filename (default: expenses.json): ") or "expenses.json"
                self.export_to_json(filename)
                
            elif choice == '10':
                self.clear_all_expenses()
                
            elif choice == '11':
                self.clear_all_budgets()
                
            elif choice == '12':
                print("Goodbye!")
                break
                
            else:
                print("Invalid choice. Please try again.")


if __name__ == "__main__":
    tracker = ExpenseTracker()
    tracker.run()