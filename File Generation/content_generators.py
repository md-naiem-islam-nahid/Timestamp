import random
import threading
from typing import List, Dict
from art import text2art, art, FONT_NAMES, ART_NAMES
import pyjokes
import random_quotes_generator
import time

class DynamicArtGenerator:
    """Generates ASCII art using the 'art' package"""
    
    def __init__(self):
        self.art_names = [name for name in ART_NAMES if len(name) > 2]
        self.fonts = [font for font in FONT_NAMES if not any(x in font.lower() for x in ['block', 'banner'])]
        self.lock = threading.Lock()
        
        # Cache some arts for better performance
        self.art_cache = []
        self.text_cache = []
        self.refresh_cache()

    def refresh_cache(self):
        """Refresh the art cache"""
        with self.lock:
            # Cache random ASCII arts
            self.art_cache = [
                art(random.choice(self.art_names))
                for _ in range(20)
            ]
            
            # Cache random text arts
            words = ['CYBER', 'QUANTUM', 'MATRIX', 'NEURAL', 'DIGITAL']
            self.text_cache = [
                text2art(random.choice(words), font=random.choice(self.fonts))
                for _ in range(20)
            ]

    def get_art(self) -> str:
        """Get a random ASCII art"""
        with self.lock:
            if not self.art_cache:
                self.refresh_cache()
            return random.choice(self.art_cache)

    def get_text_art(self) -> str:
        """Get a random text art"""
        with self.lock:
            if not self.text_cache:
                self.refresh_cache()
            return random.choice(self.text_cache)

    def generate_batch(self, count: int) -> List[str]:
        """Generate a batch of ASCII arts"""
        with self.lock:
            arts = []
            for _ in range(count):
                if random.random() > 0.5:
                    arts.append(self.get_art())
                else:
                    arts.append(self.get_text_art())
            return arts

class DynamicQuoteGenerator:
    """Generates quotes using random-quotes-generator"""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.quote_cache = []
        self.refresh_cache()

    def refresh_cache(self):
        """Refresh the quote cache"""
        with self.lock:
            self.quote_cache = [
                random_quotes_generator.get_random_quotes()
                for _ in range(50)
            ]

    def get_quote(self) -> str:
        """Get a random quote"""
        with self.lock:
            if not self.quote_cache:
                self.refresh_cache()
            return self.quote_cache.pop()

    def generate_batch(self, count: int) -> List[str]:
        """Generate a batch of quotes"""
        return [self.get_quote() for _ in range(count)]

class DynamicJokeGenerator:
    """Generates programming jokes using pyjokes"""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.joke_cache = []
        self.refresh_cache()

    def refresh_cache(self):
        """Refresh the joke cache"""
        with self.lock:
            # Get all available jokes and shuffle them
            self.joke_cache = [
                pyjokes.get_joke()
                for _ in range(50)
            ]
            random.shuffle(self.joke_cache)

    def get_joke(self) -> str:
        """Get a random joke"""
        with self.lock:
            if not self.joke_cache:
                self.refresh_cache()
            return self.joke_cache.pop()

    def generate_batch(self, count: int) -> List[str]:
        """Generate a batch of jokes"""
        return [self.get_joke() for _ in range(count)]

class DynamicContentManager:
    """Manages all dynamic content generators"""
    
    def __init__(self):
        self.art_gen = DynamicArtGenerator()
        self.quote_gen = DynamicQuoteGenerator()
        self.joke_gen = DynamicJokeGenerator()
        
        # Initialize cache
        self.cache = {
            'arts': [],
            'quotes': [],
            'jokes': [],
            'text_arts': []
        }
        self.lock = threading.Lock()
        
    def refresh_cache(self):
        """Refresh all content caches"""
        with self.lock:
            self.cache['arts'] = self.art_gen.generate_batch(20)
            self.cache['quotes'] = self.quote_gen.generate_batch(50)
            self.cache['jokes'] = self.joke_gen.generate_batch(50)
            self.cache['text_arts'] = [self.art_gen.get_text_art() for _ in range(20)]

    def get_content(self) -> Dict[str, str]:
        """Get a complete set of dynamic content"""
        with self.lock:
            if not all(self.cache.values()):
                self.refresh_cache()
            
            return {
                'art': self.cache['arts'].pop() if self.cache['arts'] else self.art_gen.get_art(),
                'quote': self.cache['quotes'].pop() if self.cache['quotes'] else self.quote_gen.get_quote(),
                'joke': self.cache['jokes'].pop() if self.cache['jokes'] else self.joke_gen.get_joke(),
                'text_art': self.cache['text_arts'].pop() if self.cache['text_arts'] else self.art_gen.get_text_art()
            }

    def get_themed_content(self, theme: str = None) -> Dict[str, str]:
        """Get themed content based on specified theme"""
        content = self.get_content()
        
        # Add themed text art
        if theme:
            try:
                content['themed_art'] = text2art(theme.upper(), 
                                               font=random.choice(self.art_gen.fonts))
            except:
                content['themed_art'] = content['text_art']
        
        return content

# Performance monitoring decorator
def monitor_performance(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        print(f"{func.__name__} took {duration:.4f} seconds")
        return result
    return wrapper

# Example usage with performance monitoring
@monitor_performance
def generate_sample_content():
    manager = DynamicContentManager()
    content = manager.get_themed_content("QUANTUM")
    return content

def main():
    """Example usage of the content generators"""
    # Create content manager
    manager = DynamicContentManager()
    
    # Get different types of content
    print("=== Regular Content ===")
    content = manager.get_content()
    print(f"Art:\n{content['art']}\n")
    print(f"Quote: {content['quote']}\n")
    print(f"Joke: {content['joke']}\n")
    print(f"Text Art:\n{content['text_art']}\n")
    
    print("=== Themed Content ===")
    themed_content = manager.get_themed_content("CYBER")
    print(f"Themed Art:\n{themed_content['themed_art']}\n")
    
    # Generate batch content
    print("=== Batch Generation ===")
    art_gen = DynamicArtGenerator()
    arts = art_gen.generate_batch(2)
    for i, art in enumerate(arts, 1):
        print(f"Art {i}:\n{art}\n")

if __name__ == "__main__":
    main()