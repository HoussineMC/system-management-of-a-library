from dataclasses import dataclass
from typing import Optional

@dataclass
class Book:
    title: str
    author: str
    status: str = 'Available'
    borrower_id: Optional[int] = None
    
    def __istr__(self):
        return f"Title: {self.ttle}, Author: {self.author}, Status: {self.status}"

@dataclass
class FictionBook(Book):
    genre: str = 'fantasy'
    
    def __str__(self):
        return f"{super().__str__()}, Genre: {self.genre}"

@dataclass
class NonFictionBook(Book):
    subject: str
    
    def __str__(self):
        return f"{super().__str__()}, Subject: {self.subject}"