import os
import tkinter as tk
from tkinter import ttk, messagebox
from dotenv import load_dotenv
import sqlite3
import csv
from datetime import datetime

from database import (
    ADMIN_USER, ADMIN_PASS,
    create_database, sign_up, login,
    add_book, get_books, borrow_book, return_book,
    get_book_types, export_books_to_file,
    get_all_users, delete_user, get_books_by_author, DATABASE_NAME
)

load_dotenv(os.path.join(os.path.dirname(__file__), 'manager.env'))

class LibraryApp:
    def __init__(self):
        create_database()
        self.window = tk.Tk()
        self.window.title("Library System")
        self.window.geometry("1000x700")
        self.current_user = None

        
        self.style = ttk.Style()
        self.style.configure('TButton', 
            font=('Helvetica', 10),
            padding=10,
            background='white',
            foreground='#0078D4',   
            borderwidth=1,
            relief='solid'
        )
        
        
        self.style.configure('Action.TButton', 
            font=('Helvetica', 10),
            padding=10,
            background='white',
            foreground='#0078D4',  
            borderwidth=1,
            relief='solid'
        )
        
        
        self.style.map('TButton',
            foreground=[
                ('active', '#0078D4'),
                ('disabled', '#666666')
            ],
            background=[
                ('active', '#f8f9fa'),
                ('disabled', '#f5f5f5')
            ],
            bordercolor=[
                ('active', '#0078D4'),
                ('!active', '#0078D4')
            ]
        )
        
        
        self.style.map('Action.TButton',
            foreground=[
                ('active', '#0078D4'),
                ('disabled', '#666666')
            ],
            background=[
                ('active', '#f8f9fa'),
                ('disabled', '#f5f5f5')
            ],
            bordercolor=[
                ('active', '#0078D4'),
                ('!active', '#0078D4')
            ]
        )
        
        
        self.style.configure('TEntry',
            fieldbackground='white',
            borderwidth=1,
            relief='solid',
            padding=5
        )
        
        
        self.window.configure(bg='white')
        self.style.configure('TFrame', background='white')

        self.show_main_menu()

    def clear_window(self):
        for widget in self.window.winfo_children():
            widget.destroy()

    def show_main_menu(self):
        self.clear_window()
        main_frame = ttk.Frame(self.window, padding="40")
        main_frame.pack(expand=True, fill="both")
        
        
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=(0, 40))
        ttk.Label(title_frame, text="Library Management System", 
                 style='Header.TLabel').pack()
        
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(expand=True)
        
        button_width = 25
        ttk.Button(button_frame, text="User Login", width=button_width,
                  style='Action.TButton', cursor='hand2', command=self.show_login_ui).pack(pady=15)
        ttk.Button(button_frame, text="Admin Login", width=button_width,
                  style='Action.TButton', cursor='hand2', command=self.show_admin_login).pack(pady=15)
        ttk.Button(button_frame, text="Exit", width=button_width,
                  cursor='hand2', command=self.window.quit).pack(pady=15)

    def show_admin_login(self):
        self.clear_window()
        login_frame = ttk.Frame(self.window, padding="20")
        login_frame.pack(expand=True)
        
        ttk.Label(login_frame, text="Admin Login", font=("Arial", 18, "bold")).pack(pady=(0, 20))
        
        ttk.Label(login_frame, text="Username:").pack()
        self.admin_username = ttk.Entry(login_frame)
        self.admin_username.pack(pady=(0, 10))
        
        ttk.Label(login_frame, text="Password:").pack()
        self.admin_password = ttk.Entry(login_frame, show="*")
        self.admin_password.pack(pady=(0, 20))
        
        ttk.Button(login_frame, text="Login", 
                  command=self.handle_admin_login).pack(pady=10)
        ttk.Button(login_frame, text="Back", 
                  command=self.show_main_menu).pack()

    def handle_admin_login(self):
        username = self.admin_username.get()
        password = self.admin_password.get()
        
        if username == ADMIN_USER and password == ADMIN_PASS:
            self.show_admin_panel()
        else:
            messagebox.showerror("Error", "Invalid admin credentials")

    def show_admin_panel(self):
        self.clear_window()
        
       
        header_frame = ttk.Frame(self.window)
        header_frame.pack(fill="x", pady=10, padx=10)
        ttk.Label(header_frame, text="Admin Panel", 
                 font=("Arial", 18, "bold")).pack(side="left")
        ttk.Button(header_frame, text="Logout", 
                  command=self.show_main_menu).pack(side="right")
        
        
        notebook = ttk.Notebook(self.window)
        notebook.pack(expand=True, fill="both", padx=10, pady=5)
        
        
        users_frame = ttk.Frame(notebook, padding=10)
        self.setup_user_management(users_frame)
        notebook.add(users_frame, text="Users")
        
        
        books_frame = ttk.Frame(notebook, padding=10)
        self.setup_admin_book_management(books_frame)
        notebook.add(books_frame, text="Books")

    def setup_admin_book_management(self, frame):
        
        controls = ttk.Frame(frame)
        controls.pack(fill="x", pady=(0, 10))
        
        ttk.Button(controls, text="Add Book", 
                  command=self.show_add_book_dialog).pack(side="left", padx=5)
        ttk.Button(controls, text="Delete Book", 
                  command=self.delete_selected_book).pack(side="left", padx=5)
        ttk.Button(controls, text="Export Books", 
                  command=self.export_books_to_file).pack(side="left", padx=5)
        
        
        search_frame = ttk.Frame(controls)
        search_frame.pack(side="right", padx=5)
        ttk.Label(search_frame, text="Search by Author:").pack(side="left")
        self.author_search = ttk.Entry(search_frame)
        self.author_search.pack(side="left", padx=5)
        ttk.Button(search_frame, text="Search", 
                  command=self.search_by_author).pack(side="left")
        
       
        self.admin_books_tree = ttk.Treeview(frame, 
            columns=('ID', 'Title', 'Author', 'Status', 'Type', 'Genre/Subject', 'Borrower'),
            show='headings')
        
        
        columns = {
            'ID': 50, 'Title': 200, 'Author': 150, 'Status': 100,
            'Type': 100, 'Genre/Subject': 150, 'Borrower': 100
        }
        for col, width in columns.items():
            self.admin_books_tree.column(col, width=width)
            self.admin_books_tree.heading(col, text=col)
        
        self.admin_books_tree.pack(fill="both", expand=True)
        self.update_admin_books_list()

    def setup_user_management(self, frame):
        self.users_tree = ttk.Treeview(frame, 
            columns=('ID', 'Username', 'Email'),
            show='headings')
            
        for col in ('ID', 'Username', 'Email'):
            self.users_tree.heading(col, text=col)
            
        self.users_tree.pack(fill="both", expand=True)
        
        ttk.Button(frame, text="Delete User", 
                  command=self.delete_selected_user).pack(pady=10)
                  
        self.update_users_list()

    def show_login_ui(self):
        self.clear_window()
        login_frame = ttk.Frame(self.window, padding="20")
        login_frame.pack(expand=True)
        
        ttk.Label(login_frame, text="User Login", 
                 font=("Arial", 18, "bold")).pack(pady=(0, 20))
        
        ttk.Label(login_frame, text="Username:").pack()
        self.username = ttk.Entry(login_frame)
        self.username.pack(pady=(0, 10))
        
        ttk.Label(login_frame, text="Password:").pack()
        self.password = ttk.Entry(login_frame, show="*")
        self.password.pack(pady=(0, 20))
        
        button_frame = ttk.Frame(login_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Login", 
                  command=self.handle_user_login).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Sign Up", 
                  command=self.show_signup_ui).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Back", 
                  command=self.show_main_menu).pack(side="left", padx=5)

    def show_signup_ui(self):
        self.clear_window()
        signup_frame = ttk.Frame(self.window, padding="20")
        signup_frame.pack(expand=True)
        
        ttk.Label(signup_frame, text="Sign Up", 
                 font=("Arial", 18, "bold")).pack(pady=(0, 20))
        
        ttk.Label(signup_frame, text="Username:").pack()
        self.new_username = ttk.Entry(signup_frame)
        self.new_username.pack(pady=(0, 10))
        
        ttk.Label(signup_frame, text="Password:").pack()
        self.new_password = ttk.Entry(signup_frame, show="*")
        self.new_password.pack(pady=(0, 10))
        
        ttk.Label(signup_frame, text="Email:").pack()
        self.email = ttk.Entry(signup_frame)
        self.email.pack(pady=(0, 20))
        
        ttk.Button(signup_frame, text="Sign Up", 
                  command=self.handle_signup).pack(pady=10)
        ttk.Button(signup_frame, text="Back", 
                  command=self.show_login_ui).pack()

    def handle_signup(self):
        username = self.new_username.get().strip()
        password = self.new_password.get().strip()
        email = self.email.get().strip()
        
        if not username or not password or not email:
            messagebox.showerror("Error", "Please fill all fields")
            return
            
        try:
            success = sign_up(username, password, email)
            if success:
                messagebox.showinfo("Success", "Account created successfully!")
                self.show_login_ui()  
                
            else:
                messagebox.showerror("Error", "Username already exists")
        except Exception as e:
            messagebox.showerror("Error", f"Registration failed: {str(e)}")

    def handle_user_login(self):
        username = self.username.get()
        password = self.password.get()
        user = login(username, password)
        
        if user:
            self.current_user = user
            self.show_user_panel()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def show_user_panel(self):
        self.clear_window()
        
        
        header_frame = ttk.Frame(self.window, style='Header.TFrame')
        header_frame.pack(fill="x", pady=10, padx=20)
        
        welcome_label = ttk.Label(header_frame, 
                                text=f"Welcome {self.current_user['username']}", 
                                style='Title.TLabel')
        welcome_label.pack(side="left")
        
        
        logout_btn = ttk.Button(header_frame, text="Logout", 
                              style='Action.TButton', cursor='hand2', command=self.show_main_menu)
        logout_btn.pack(side="right")
        
        
        books_frame = ttk.Frame(self.window, padding=20)
        books_frame.pack(expand=True, fill="both", padx=20, pady=10)
        
        
        actions = ttk.Frame(books_frame)
        actions.pack(fill="x", pady=(0, 15))
        ttk.Button(actions, text="Borrow Book", style='Action.TButton',
                  cursor='hand2', command=self.borrow_book).pack(side="left", padx=5)
        ttk.Button(actions, text="Return Book", style='Action.TButton',
                  cursor='hand2', command=self.return_book).pack(side="left", padx=5)
        
        
        self.books_tree = ttk.Treeview(books_frame, 
            columns=('ID', 'Title', 'Author', 'Status', 'Borrower'),
            show='headings', style='Treeview')
        
        
        self.books_tree.column('ID', width=50, anchor='center')
        self.books_tree.column('Title', width=250, anchor='w')
        self.books_tree.column('Author', width=200, anchor='w')
        self.books_tree.column('Status', width=100, anchor='center')
        self.books_tree.column('Borrower', width=150, anchor='w')
        
        for col in ('ID', 'Title', 'Author', 'Status', 'Borrower'):
            self.books_tree.heading(col, text=col)
        
       
        scrollbar = ttk.Scrollbar(books_frame, orient="vertical", 
                                command=self.books_tree.yview)
        self.books_tree.configure(yscrollcommand=scrollbar.set)
        
        self.books_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.update_books_list()

    def update_books_list(self):
        for item in self.books_tree.get_children():
            self.books_tree.delete(item)
        books = get_books()
        for book in books:
            self.books_tree.insert('', 'end', values=book)
        
        self.books_tree.update()

    def update_users_list(self):
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        users = get_all_users()
        for user in users:
            self.users_tree.insert('', 'end', values=user)

    def update_admin_books_list(self):
        for item in self.admin_books_tree.get_children():
            self.admin_books_tree.delete(item)
        books = get_books()
        for book in books:
            self.admin_books_tree.insert('', 'end', values=book)

    def show_add_book_dialog(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Add New Book")
        dialog.geometry("400x500")
        dialog.transient(self.window)
        dialog.grab_set()  
        
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        
        ttk.Label(main_frame, text="Title:*").pack(fill='x')
        title_entry = ttk.Entry(main_frame)
        title_entry.pack(fill='x', pady=(0, 10))
        
        
        ttk.Label(main_frame, text="Author:*").pack(fill='x')
        author_entry = ttk.Entry(main_frame)
        author_entry.pack(fill='x', pady=(0, 10))
        
        
        ttk.Label(main_frame, text="Book Type:*").pack(fill='x')
        book_type = tk.StringVar(value="fiction")
        ttk.Radiobutton(main_frame, text="Fiction", 
                       variable=book_type, 
                       value="fiction").pack()
        ttk.Radiobutton(main_frame, text="Non-Fiction", 
                       variable=book_type, 
                       value="non-fiction").pack(pady=(0, 10))
        
        
        ttk.Label(main_frame, text="Genre/Subject:").pack(fill='x')
        genre_subject_entry = ttk.Entry(main_frame)
        genre_subject_entry.pack(fill='x', pady=(0, 20))
        
        def add():
            title = title_entry.get().strip()
            author = author_entry.get().strip()
            genre_subject = genre_subject_entry.get().strip()
            
            if not title or not author:
                messagebox.showerror("Error", "Title and Author are required")
                return
            
            print(f"Attempting to add book: {title=}, {author=}")  
            
            try:
                result = add_book(
                    title=title,
                    author=author,
                    book_type=book_type.get(),
                    genre_or_subject=genre_subject
                )
                
                if result:
                    messagebox.showinfo("Success", "Book added successfully")
                    self.update_admin_books_list()
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Failed to add book")
            except Exception as e:
                messagebox.showerror("Error", f"Error adding book: {str(e)}")
        
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(20, 0))
        ttk.Button(button_frame, text="Add", command=add).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=dialog.destroy).pack(side='left', padx=5)
        
        
        ttk.Label(main_frame, text="* Required fields", 
                 font=("Arial", 8)).pack(pady=(20, 0))
        
        
        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - dialog.winfo_width()) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

    def delete_selected_book(self):
        try:
            selection = self.admin_books_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a book to delete")
                return
                
            if messagebox.askyesno("Confirm", "Delete selected book?"):
                book_id = self.admin_books_tree.item(selection[0])['values'][0]
                
                
                conn = sqlite3.connect(DATABASE_NAME)
                cursor = conn.cursor()
                
                
                cursor.execute("DELETE FROM books WHERE book_id = ?", (book_id,))
                conn.commit()
                
                
                if cursor.rowcount > 0:
                    
                    self.admin_books_tree.delete(selection[0])
                    
                    
                    self.update_admin_books_list()
                    if hasattr(self, 'books_tree'):
                        self.update_books_list()
                        
                    messagebox.showinfo("Success", "Book deleted successfully")
                else:
                    messagebox.showerror("Error", "Book not found in database")
                    
                conn.close()
                
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Database error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete book: {str(e)}")
            print(f"Error details: {str(e)}")  

    def export_books_to_file(self):
        try:
            
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            
            
            cursor.execute("""
                SELECT b.book_id, b.title, b.author, b.status, 
                       b.book_type, b.genre_or_subject,
                       COALESCE(u.username, '-') as borrower
                FROM books b
                LEFT JOIN users u ON b.borrower_id = u.user_id
            """)
            books = cursor.fetchall()
        
            filename = f"library_books_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                writer.writerow(['ID', 'Title', 'Author', 'Status', 
                               'Type', 'Genre/Subject', 'Borrower'])
                
                writer.writerows(books)
            
            conn.close()
            messagebox.showinfo("Success", f"Books exported to {filename}")
            
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Database error: {str(e)}")
            print(f"Database error details: {str(e)}")  
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export books: {str(e)}")
            print(f"Error details: {str(e)}") 

    def delete_selected_user(self):
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user to delete")
            return
            
        if messagebox.askyesno("Confirm", "Delete selected user?"):
            user_id = self.users_tree.item(selection[0])['values'][0]
            if delete_user(user_id):
                self.update_users_list()
                messagebox.showinfo("Success", "User deleted successfully")
            else:
                messagebox.showerror("Error", "Failed to delete user")

    def borrow_book(self):
        selection = self.books_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a book to borrow")
            return
            
        book_data = self.books_tree.item(selection[0])['values']
        book_id = book_data[0]
        status = book_data[3]
        
        if status != 'Available':
            messagebox.showerror("Error", "This book is not available")
            return
            
        if borrow_book(self.current_user, book_id):
            self.update_books_list()
            self.update_admin_books_list()   
            messagebox.showinfo("Success", "Book borrowed successfully")
        else:
            messagebox.showerror("Error", "Could not borrow book")

    def return_book(self):
        selection = self.books_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a book to return")
            return
        
        try:
            book_data = self.books_tree.item(selection[0])['values']
            book_id = book_data[0]  
            
            
            print(f"Attempting to return book: {book_id} by user: {self.current_user['username']}")
            
            if return_book(self.current_user['user_id'], book_id):
                self.update_books_list()
                messagebox.showinfo("Success", "Book returned successfully")
            else:
                messagebox.showerror("Error", "Could not return book. Make sure you borrowed this book.")
        except Exception as e:
            messagebox.showerror("Error", f"Error returning book: {str(e)}")
            print(f"Error details: {str(e)}")  

    def search_by_author(self):
        author = self.author_search.get().strip()
        if not author:
            messagebox.showwarning("Warning", "Please enter an author name")
            return
            
        books = get_books_by_author(author)
        
        
        for item in self.admin_books_tree.get_children():
            self.admin_books_tree.delete(item)
            
        
        for book in books:
            self.admin_books_tree.insert('', 'end', values=book)

if __name__ == "__main__":
    app = LibraryApp()
    app.window.mainloop()