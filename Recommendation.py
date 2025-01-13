import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple

class LearningContentRecommender:
    def __init__(self):
        # Learning style weights for different content types
        self.content_style_weights = {
            'video_tutorial': {
                'visual': 0.9,
                'auditory': 0.7,
                'kinesthetic': 0.3,
                'social': 0.4,
                'logical': 0.5,
                'read_write': 0.3
            },
            'interactive_simulation': {
                'visual': 0.8,
                'auditory': 0.2,
                'kinesthetic': 0.9,
                'social': 0.3,
                'logical': 0.7,
                'read_write': 0.4
            },
            'textbook': {
                'visual': 0.5,
                'auditory': 0.1,
                'kinesthetic': 0.2,
                'social': 0.1,
                'logical': 0.8,
                'read_write': 0.9
            },
            'group_project': {
                'visual': 0.5,
                'auditory': 0.7,
                'kinesthetic': 0.7,
                'social': 0.9,
                'logical': 0.6,
                'read_write': 0.5
            },
            'practice_exercises': {
                'visual': 0.6,
                'auditory': 0.3,
                'kinesthetic': 0.8,
                'social': 0.2,
                'logical': 0.9,
                'read_write': 0.7
            },
            'audio_lecture': {
                'visual': 0.2,
                'auditory': 0.9,
                'kinesthetic': 0.1,
                'social': 0.3,
                'logical': 0.6,
                'read_write': 0.4
            }
        }
        
    def create_content_database(self, content_items: List[Dict]) -> pd.DataFrame:
        """
        Create a database of educational content with their properties.
        
        Args:
            content_items: List of dictionaries containing content information
                         Each dict should have: id, title, type, subject, difficulty
        
        Returns:
            DataFrame with content items and their style weights
        """
        df = pd.DataFrame(content_items)
        
        # Add learning style weights based on content type
        for style in ['visual', 'auditory', 'kinesthetic', 'social', 'logical', 'read_write']:
            df[f'{style}_weight'] = df['type'].map(
                lambda x: self.content_style_weights[x][style]
            )
            
        return df
    
    def get_user_profile(self, 
                        learning_style_scores: Dict[str, float],
                        subject_preferences: Dict[str, float],
                        difficulty_preference: float) -> np.ndarray:
        """
        Create a user profile vector based on their learning preferences.
        
        Args:
            learning_style_scores: Dictionary of learning style scores (0-1)
            subject_preferences: Dictionary of subject preferences (0-1)
            difficulty_preference: Preferred difficulty level (0-1)
            
        Returns:
            numpy array representing user preferences
        """
        profile = []
        
        # Add learning style scores
        for style in ['visual', 'auditory', 'kinesthetic', 'social', 'logical', 'read_write']:
            profile.append(learning_style_scores.get(style, 0.5))
            
        # Add subject preferences
        for subject in subject_preferences:
            profile.append(subject_preferences[subject])
            
        # Add difficulty preference
        profile.append(difficulty_preference)
        
        return np.array(profile)
    
    def get_content_vector(self, content: pd.Series) -> np.ndarray:
        """
        Create a vector representation of a content item.
        """
        vector = []
        
        # Add learning style weights
        for style in ['visual', 'auditory', 'kinesthetic', 'social', 'logical', 'read_write']:
            vector.append(content[f'{style}_weight'])
            
        # Add subject indicator (one-hot)
        subjects = self.content_database['subject'].unique()
        for subject in subjects:
            vector.append(1.0 if content['subject'] == subject else 0.0)
            
        # Add difficulty
        vector.append(content['difficulty'])
        
        return np.array(vector)
    
    def recommend(self, 
                 user_profile: Dict,
                 n_recommendations: int = 5,
                 exclude_ids: List[str] = None) -> List[Tuple[str, float]]:
        """
        Recommend content based on user profile and learning preferences.
        
        Args:
            user_profile: Dictionary containing learning_style_scores, 
                        subject_preferences, and difficulty_preference
            n_recommendations: Number of recommendations to return
            exclude_ids: List of content IDs to exclude
            
        Returns:
            List of tuples (content_id, similarity_score)
        """
        exclude_ids = exclude_ids or []
        
        # Create user profile vector
        user_vector = self.get_user_profile(
            user_profile['learning_style_scores'],
            user_profile['subject_preferences'],
            user_profile['difficulty_preference']
        )
        
        # Calculate similarity scores
        similarities = []
        for _, content in self.content_database.iterrows():
            if content['id'] not in exclude_ids:
                content_vector = self.get_content_vector(content)
                similarity = cosine_similarity(
                    user_vector.reshape(1, -1),
                    content_vector.reshape(1, -1)
                )[0][0]
                similarities.append((content['id'], similarity))
        
        # Sort by similarity and return top N
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:n_recommendations]

    def get_content_details(self, content_id: str) -> Dict:
        """
        Get detailed information about a specific content item.
        """
        content = self.content_database[self.content_database['id'] == content_id].iloc[0]
        return {
            'id': content['id'],
            'title': content['title'],
            'type': content['type'],
            'subject': content['subject'],
            'difficulty': content['difficulty']
        }

# Example usage
recommender = LearningContentRecommender()

# Create sample content database
sample_content = [
    {
        'id': 'c1',
        'title': 'Interactive Physics Lab',
        'type': 'interactive_simulation',
        'subject': 'physics',
        'difficulty': 0.7
    },
    {
        'id': 'c2',
        'title': 'History Video Series',
        'type': 'video_tutorial',
        'subject': 'history',
        'difficulty': 0.5
    },
    # Add more content items...
]

recommender.content_database = recommender.create_content_database(sample_content)

# Example user profile
user_profile = {
    'learning_style_scores': {
        'visual': 0.8,
        'auditory': 0.4,
        'kinesthetic': 0.7,
        'social': 0.6,
        'logical': 0.9,
        'read_write': 0.5
    },
    'subject_preferences': {
        'physics': 0.9,
        'history': 0.6
    },
    'difficulty_preference': 0.7
}

# Get recommendations
recommendations = recommender.recommend(user_profile, n_recommendations=3)