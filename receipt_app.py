from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
import matplotlib.pyplot as plt
from kivy.uix.popup import Popup
import sqlite3
import io
from PIL import Image as PILImage


def create_database():
    conn = sqlite3.connect("finance_tracker.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        amount REAL,
        category TEXT,
        date TEXT
    )''')
    conn.commit()
    conn.close()


class FinanceTrackerApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(DashboardScreen(name="dashboard"))
        sm.add_widget(AddExpenseScreen(name="add_expense"))
        sm.add_widget(ViewReportScreen(name="view_report"))
        return sm


class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super(DashboardScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        dashboard_label = Label(text="Finance Tracker Dashboard", font_size=24)
        layout.add_widget(dashboard_label)

        btn_add_expense = Button(text="Add Expense", size_hint=(0.5, 0.1))
        btn_add_expense.bind(on_press=self.go_to_add_expense)
        layout.add_widget(btn_add_expense)

        btn_view_report = Button(text="View Report", size_hint=(0.5, 0.1))
        btn_view_report.bind(on_press=self.go_to_view_report)
        layout.add_widget(btn_view_report)

        self.add_widget(layout)

    def go_to_add_expense(self, instance):
        self.manager.current = 'add_expense'

    def go_to_view_report(self, instance):
        self.manager.current = 'view_report'


class AddExpenseScreen(Screen):
    def __init__(self, **kwargs):
        super(AddExpenseScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.name_input = TextInput(hint_text="Expense Name", multiline=False, size_hint=(1, 0.1))
        self.amount_input = TextInput(hint_text="Amount", multiline=False, input_filter='float', size_hint=(1, 0.1))
        self.category_input = TextInput(hint_text="Category", multiline=False, size_hint=(1, 0.1))

        layout.add_widget(self.name_input)
        layout.add_widget(self.amount_input)
        layout.add_widget(self.category_input)

        btn_save = Button(text="Save Expense", size_hint=(0.5, 0.1))
        btn_save.bind(on_press=self.save_expense)
        layout.add_widget(btn_save)

        btn_back = Button(text="Back to Dashboard", size_hint=(0.5, 0.1))
        btn_back.bind(on_press=self.go_to_dashboard)
        layout.add_widget(btn_back)

        self.add_widget(layout)

    def save_expense(self, instance):
        name = self.name_input.text.strip()
        amount = self.amount_input.text.strip()
        category = self.category_input.text.strip()

        if name and amount and category:
            try:
                conn = sqlite3.connect("finance_tracker.db")
                c = conn.cursor()
                c.execute("INSERT INTO expenses (name, amount, category, date) VALUES (?, ?, ?, datetime('now'))",
                          (name, float(amount), category))
                conn.commit()
                conn.close()

                self.name_input.text = ""
                self.amount_input.text = ""
                self.category_input.text = ""
                popup = Popup(title="Success", content=Label(text="Expense saved!"), size_hint=(0.6, 0.4))
                popup.open()
            except Exception as e:
                popup = Popup(title="Error", content=Label(text=f"Failed to save expense: {e}"), size_hint=(0.6, 0.4))
                popup.open()
        else:
            popup = Popup(title="Error", content=Label(text="Please fill out all fields"), size_hint=(0.6, 0.4))
            popup.open()

    def go_to_dashboard(self, instance):
        self.manager.current = 'dashboard'


class ViewReportScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        
        self.chart_image = Image(size_hint=(1, 0.7))
        layout.add_widget(self.chart_image)

        # buttons
        btn_generate = Button(text="Generate Report", size_hint=(1, 0.15))
        btn_generate.bind(on_press=self.generate_report)
        layout.add_widget(btn_generate)

        btn_back = Button(text="Back to Dashboard", size_hint=(1, 0.15))
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_back)

        self.add_widget(layout)

    def go_back(self, instance):
        self.manager.current = "dashboard"

    def generate_report(self, instance):
        try:

            conn = sqlite3.connect("finance_tracker.db")
            c = conn.cursor()
            c.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
            data = c.fetchall()
            conn.close()

            if not data:
                popup = Popup(title="No Data", content=Label(text="No expenses to generate a report."), size_hint=(0.6, 0.4))
                popup.open()
                return

            categories, amounts = zip(*data)

            # pie chart
            plt.figure(figsize=(4, 4), dpi=100)
            plt.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=90)
            plt.title("Expense Distribution")
            plt.tight_layout()

            # chart to buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            buffer.seek(0)
            plt.close()

            # chart into a texture
            pil_image = PILImage.open(buffer)
            texture = Texture.create(size=pil_image.size, colorfmt='rgba')
            texture.blit_buffer(pil_image.tobytes(), colorfmt='rgba', bufferfmt='ubyte')
            texture.flip_vertical()

            # texture to chart_image
            self.chart_image.texture = texture
        except Exception as e:
            popup = Popup(title="Error", content=Label(text=f"Failed to generate report: {e}"), size_hint=(0.6, 0.4))
            popup.open()


    def go_to_dashboard(self, instance):
        self.manager.current = 'dashboard'


if __name__ == "__main__":
    create_database()
    FinanceTrackerApp().run()
