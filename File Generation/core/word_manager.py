import os
import random
import string
import threading
from typing import List, Dict, Set
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

class WordManager:
    """
    Manages word lists with efficient caching and thread-safe operations.
    Provides fast access to words and pre-generated combinations.
    """
    
    def __init__(self, word_lists_dir: str = "word_lists"):
        """
        Initialize WordManager with word list directory.
        
        Args:
            word_lists_dir (str): Directory containing word list files
        """
        self.word_lists_dir = Path(word_lists_dir)
        self.categories = ['primary', 'secondary', 'technical']
        
        # Thread-safe storage
        self._word_lists: Dict[str, List[str]] = {}
        self._combinations: Dict[str, List[str]] = {}
        self._used_combinations: Dict[str, Set[str]] = {}
        self._locks = {
            'word_lists': threading.Lock(),
            'combinations': threading.Lock(),
            'used': threading.Lock()
        }
        
        # Initialize caches
        self._load_word_lists()
        self._generate_combinations()
        
    def _load_word_lists(self) -> None:
        """Load word lists from files with parallel processing."""
        def load_category(category: str) -> tuple[str, List[str]]:
            file_path = self.word_lists_dir / f"{category}.txt"
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    # Filter empty lines and strip whitespace
                    words = [word.strip() for word in f.readlines() if word.strip()]
                    # Remove duplicates while preserving order
                    seen = set()
                    unique_words = [x for x in words if not (x in seen or seen.add(x))]
                    return category, unique_words
            except Exception as e:
                print(f"Error loading {category} word list: {e}")
                return category, ["default"]

        # Load word lists in parallel
        with ThreadPoolExecutor() as executor:
            results = executor.map(load_category, self.categories)
            
        with self._locks['word_lists']:
            self._word_lists.update(dict(results))
    
    def _generate_combinations(self, cache_size: int = 10000) -> None:
        """
        Pre-generate word combinations for faster access.
        Uses parallel processing for generation.
        
        Args:
            cache_size (int): Number of combinations to cache per category
        """
        def generate_for_category(category: str) -> tuple[str, List[str]]:
            words = self._word_lists[category]
            combinations = []
            
            for _ in range(cache_size):
                word = random.choice(words)
                letter = random.choice(string.ascii_letters)
                number = random.randint(100, 999)
                combination = f"{word}_{letter}{number}"
                combinations.append(combination)
            
            return category, combinations
        
        # Generate combinations in parallel
        with ThreadPoolExecutor() as executor:
            results = executor.map(generate_for_category, self.categories)
            
        with self._locks['combinations']:
            self._combinations.update(dict(results))
            
        # Initialize used combinations tracking
        with self._locks['used']:
            self._used_combinations = {category: set() for category in self.categories}
    
    def get_word(self, category: str) -> str:
        """
        Get a unique word combination that hasn't been used before.
        Thread-safe access to combinations.
        
        Args:
            category (str): Word list category to use
            
        Returns:
            str: Unique word combination
        """
        if category not in self.categories:
            category = 'primary'
            
        with self._locks['combinations'], self._locks['used']:
            combinations = self._combinations[category]
            used = self._used_combinations[category]
            
            # Find unused combination
            for _ in range(len(combinations)):
                combination = random.choice(combinations)
                if combination not in used:
                    used.add(combination)
                    return combination
            
            # If all combinations are used, regenerate
            self._generate_combinations()
            return self.get_word(category)
    
    def get_random_text(self, length: int = 8) -> str:
        """
        Generate random text of specified length.
        Uses pre-generated character sets for efficiency.
        
        Args:
            length (int): Length of random text
            
        Returns:
            str: Random text string
        """
        return ''.join(random.choices(string.ascii_uppercase, k=length))
    
    def get_random_digits(self, length: int = 10) -> str:
        """
        Generate random digits of specified length.
        Uses pre-generated digit sets for efficiency.
        
        Args:
            length (int): Length of digit string
            
        Returns:
            str: Random digit string
        """
        return ''.join(random.choices(string.digits, k=length))
    
    def refresh_combinations(self) -> None:
        """
        Refresh combination caches.
        Called periodically or when combinations are depleted.
        """
        self._generate_combinations()
        
    def get_statistics(self) -> Dict[str, int]:
        """
        Get usage statistics for monitoring.
        
        Returns:
            Dict[str, int]: Statistics about word usage
        """
        with self._locks['used']:
            return {
                category: len(used)
                for category, used in self._used_combinations.items()
            }

# Example usage
if __name__ == "__main__":
    # Initialize word manager
    word_manager = WordManager()
    
    # Generate some example combinations
    print("Example word combinations:")
    for category in ['primary', 'secondary', 'technical']:
        words = [word_manager.get_word(category) for _ in range(5)]
        print(f"{category.capitalize()} words: {words}")
    
    # Generate random components
    print("\nRandom components:")
    print(f"Random text: {word_manager.get_random_text()}")
    print(f"Random digits: {word_manager.get_random_digits()}")
    
    # Show statistics
    print("\nUsage statistics:")
    print(word_manager.get_statistics())