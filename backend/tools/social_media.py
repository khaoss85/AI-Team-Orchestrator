import logging
import json
import re
import time
import random
from typing import List, Dict, Any, Optional, Union
from uuid import UUID
import asyncio

# Import dal pacchetto OpenAI Agents
from agents import function_tool

logger = logging.getLogger(__name__)

class InstagramTools:
    """Tools for Instagram analysis and management"""
    
    @staticmethod
    @function_tool
    async def analyze_hashtags(hashtags_json: str) -> str:
        """
        Analyze Instagram hashtags for popularity and relevance.
        
        Args:
            hashtags_json: JSON string list of hashtags to analyze (without # symbol)
        
        Returns:
            Analysis results as JSON string
        """
        try:
            # Parse hashtags from JSON string
            hashtags = json.loads(hashtags_json)
            
            logger.info(f"Analyzing hashtags: {', '.join(hashtags)}")
            
            # In a real implementation, this would call an Instagram API or use web scraping
            # For now, we'll return simulated data
            
            results = {}
            for hashtag in hashtags:
                # Simulate API call delay
                await asyncio.sleep(0.5)
                
                # Generate random stats for this example
                post_count = random.randint(10000, 10000000)
                engagement_rate = round(random.uniform(0.5, 5.0), 2)
                growth_rate = round(random.uniform(-2.0, 10.0), 2)
                
                # Determine if trending based on growth rate
                trending = growth_rate > 3.0
                
                # Generate related tags
                all_possible_related = ["travel", "photography", "instagood", "love", 
                                        "fashion", "photooftheday", "art", "beautiful", 
                                        "nature", "picoftheday", "happy", "follow", 
                                        "style", "instadaily", "reels", "viral"]
                related_tags = random.sample(all_possible_related, min(5, len(all_possible_related)))
                
                results[hashtag] = {
                    "posts_count": post_count,
                    "engagement_rate": f"{engagement_rate}%",
                    "growth_rate": f"{growth_rate}%",
                    "trending": trending,
                    "popularity_score": round(min(post_count / 1000000, 1) * 10, 1),
                    "related_tags": related_tags,
                    "best_posting_times": ["9:00 AM", "6:00 PM", "9:00 PM"]
                }
            
            # Add overall assessment
            if hashtags:
                top_hashtag = max(hashtags, key=lambda h: results[h]["popularity_score"])
                trending_hashtags = [h for h in hashtags if results[h]["trending"]]
                
                results["analysis"] = {
                    "top_performing_hashtag": top_hashtag,
                    "trending_hashtags": trending_hashtags,
                    "recommendation": "Use a mix of highly popular and niche hashtags for best reach"
                }
            
            return json.dumps(results)
        except Exception as e:
            logger.error(f"Error analyzing hashtags: {e}")
            return json.dumps({"error": str(e)})
    
    @staticmethod
    @function_tool
    async def analyze_account(username: str) -> str:
        """
        Analyze an Instagram account for engagement metrics.
        
        Args:
            username: Instagram username without @ symbol
        
        Returns:
            Dictionary with account analysis as JSON string
        """
        try:
            logger.info(f"Analyzing Instagram account: {username}")
            
            # In a real implementation, this would use Instagram API or web scraping
            # For now, simulate the analysis
            
            # Simulate API call delay
            await asyncio.sleep(1)
            
            # Generate random stats
            followers = random.randint(1000, 1000000)
            following = random.randint(100, 5000)
            posts = random.randint(10, 1000)
            engagement_rate = round(random.uniform(0.5, 8.0), 2)
            
            # Generate random post type distribution
            post_types = {
                "images": round(random.uniform(40, 80), 1),
                "videos": round(random.uniform(10, 50), 1),
                "carousels": round(random.uniform(5, 30), 1)
            }
            
            # Normalize to 100%
            total = sum(post_types.values())
            for key in post_types:
                post_types[key] = round((post_types[key] / total) * 100, 1)
            
            # Generate posting frequency
            posting_frequency = random.choice(["daily", "2-3 times per week", "weekly", "bi-weekly", "monthly"])
            
            # Generate top hashtags
            all_possible_hashtags = ["travel", "photography", "instagood", "love", 
                                    "fashion", "photooftheday", "art", "beautiful", 
                                    "nature", "picoftheday", "happy", "follow"]
            top_hashtags = random.sample(all_possible_hashtags, min(5, len(all_possible_hashtags)))
            
            # Create analysis report
            account_info = {
                "username": username,
                "followers_count": followers,
                "following_count": following,
                "posts_count": posts,
                "engagement_rate": f"{engagement_rate}%",
                "post_types_distribution": post_types,
                "posting_frequency": posting_frequency,
                "top_hashtags": top_hashtags,
                "best_performing_content": {
                    "type": random.choice(["video", "carousel", "image"]),
                    "average_likes": int(followers * random.uniform(0.05, 0.2)),
                    "average_comments": int(followers * random.uniform(0.001, 0.01))
                },
                "growth_trend": random.choice(["increasing", "stable", "decreasing"]),
                "audience_demographics": {
                    "age_groups": {
                        "18-24": round(random.uniform(10, 40), 1),
                        "25-34": round(random.uniform(20, 50), 1),
                        "35-44": round(random.uniform(10, 30), 1),
                        "45+": round(random.uniform(5, 20), 1)
                    },
                    "gender_split": {
                        "male": round(random.uniform(30, 70), 1),
                        "female": None  # Will be calculated
                    }
                }
            }
            
            # Calculate the female percentage to make it sum to 100%
            account_info["audience_demographics"]["gender_split"]["female"] = round(
                100 - account_info["audience_demographics"]["gender_split"]["male"], 1
            )
            
            return json.dumps(account_info)
        except Exception as e:
            logger.error(f"Error analyzing account: {e}")
            return json.dumps({"error": str(e)})
    
    @staticmethod
    @function_tool
    async def generate_content_ideas(topic: str, target_audience: str, count: int = 5) -> str:
        """
        Generate content ideas for Instagram based on topic and target audience.
        
        Args:
            topic: The main topic or niche (e.g., "fitness", "fashion")
            target_audience: Description of the target audience (e.g., "young adults interested in sustainable fashion")
            count: Number of ideas to generate
            
        Returns:
            List of content ideas with details as JSON string
        """
        try:
            logger.info(f"Generating {count} content ideas for topic: {topic}, audience: {target_audience}")
            
            # Simulate thinking time
            await asyncio.sleep(1.5)
            
            # Content types to choose from
            content_types = [
                "Carousel post", "Single image", "Video", "Reel", "Story", "IGTV"
            ]
            
            # Generate ideas based on topic
            ideas = []
            for i in range(count):
                content_type = random.choice(content_types)
                
                if topic.lower() == "fitness":
                    themes = [
                        "Workout routine", "Healthy meal prep", "Before and after transformation",
                        "Fitness tips", "Exercise tutorial", "Motivational quote"
                    ]
                    theme = random.choice(themes)
                    
                elif topic.lower() == "fashion":
                    themes = [
                        "Outfit of the day", "Fashion haul", "Style guide", "Seasonal trends",
                        "Sustainable fashion", "Accessory styling"
                    ]
                    theme = random.choice(themes)
                    
                elif topic.lower() == "food":
                    themes = [
                        "Recipe walkthrough", "Restaurant review", "Food photography",
                        "Cooking tips", "Ingredient spotlight", "Meal ideas"
                    ]
                    theme = random.choice(themes)
                    
                else:
                    themes = [
                        "How-to guide", "Day in the life", "Product review", "Top tips",
                        "Behind the scenes", "Q&A session", "Trending topic discussion"
                    ]
                    theme = random.choice(themes)
                
                # Generate hashtags
                hashtags = [f"#{topic.lower()}", f"#instagram", f"#{theme.lower().replace(' ', '')}"]
                additional_hashtags = ["#trending", "#viral", "#instagood", "#follow", "#love", "#photooftheday"]
                hashtags.extend(random.sample(additional_hashtags, 3))
                
                # Build the idea
                idea = {
                    "title": f"{theme} {content_type}",
                    "description": f"Create a {content_type.lower()} about {theme.lower()} targeting {target_audience}",
                    "content_type": content_type,
                    "theme": theme,
                    "hashtags": hashtags,
                    "estimated_engagement": f"{random.randint(1, 5)}/5",
                    "best_posting_time": random.choice(["Morning (9AM)", "Afternoon (2PM)", "Evening (6PM)", "Night (9PM)"]),
                    "visual_elements": ["Bright colors", "Clear text", "High-quality imagery", "Authentic feel"]
                }
                
                ideas.append(idea)
            
            return json.dumps(ideas)
        except Exception as e:
            logger.error(f"Error generating content ideas: {e}")
            return json.dumps({"error": str(e)})
    
    @staticmethod
    @function_tool
    async def analyze_competitors(usernames_json: str) -> str:
        """
        Analyze competitor Instagram accounts and their strategies.
        
        Args:
            usernames_json: JSON string list of Instagram usernames to analyze
            
        Returns:
            Dictionary with competitor analysis as JSON string
        """
        try:
            # Parse usernames from JSON string
            usernames = json.loads(usernames_json)
            
            logger.info(f"Analyzing competitors: {', '.join(usernames)}")
            
            # In a real implementation, this would analyze real accounts
            # For now, generate simulated data
            
            competitor_data = {}
            overall_insights = {}
            
            for username in usernames:
                # Simulate API delay
                await asyncio.sleep(0.8)
                
                # Generate random stats
                followers = random.randint(5000, 2000000)
                posts = random.randint(50, 2000)
                engagement_rate = round(random.uniform(0.5, 10.0), 2)
                post_frequency = random.choice(["daily", "2-3 times per week", "weekly", "bi-weekly"])
                
                # Generate content mix
                content_mix = {
                    "product_showcases": round(random.uniform(10, 60), 1),
                    "lifestyle_content": round(random.uniform(10, 40), 1),
                    "user_generated_content": round(random.uniform(0, 30), 1),
                    "educational_content": round(random.uniform(0, 40), 1)
                }
                
                # Normalize to 100%
                total = sum(content_mix.values())
                for key in content_mix:
                    content_mix[key] = round((content_mix[key] / total) * 100, 1)
                
                # Create competitor profile
                competitor_data[username] = {
                    "followers_count": followers,
                    "posts_count": posts,
                    "engagement_rate": f"{engagement_rate}%",
                    "posting_frequency": post_frequency,
                    "content_mix": content_mix,
                    "top_performing_content": random.choice(["product showcases", "lifestyle content", "educational content"]),
                    "strengths": random.sample(["Consistent branding", "High-quality visuals", "Strong community engagement", 
                                            "Effective use of stories", "Collaborations", "User-generated content"], 2),
                    "weaknesses": random.sample(["Irregular posting", "Low engagement on certain content", 
                                            "Limited use of video", "Weak call-to-actions", "Poor hashtag strategy"], 2)
                }
            
            # Generate overall insights if we have competitors
            if competitor_data:
                # Find average followers and engagement
                avg_followers = sum(data["followers_count"] for data in competitor_data.values()) / len(competitor_data)
                avg_engagement = sum(float(data["engagement_rate"].strip("%")) for data in competitor_data.values()) / len(competitor_data)
                
                # Find most common posting frequency
                frequencies = [data["posting_frequency"] for data in competitor_data.values()]
                most_common_frequency = max(set(frequencies), key=frequencies.count)
                
                # Determine most effective content type
                top_performing = [data["top_performing_content"] for data in competitor_data.values()]
                most_effective_content = max(set(top_performing), key=top_performing.count)
                
                overall_insights = {
                    "average_followers": int(avg_followers),
                    "average_engagement_rate": f"{round(avg_engagement, 2)}%",
                    "most_common_posting_frequency": most_common_frequency,
                    "most_effective_content_type": most_effective_content,
                    "opportunity_areas": random.sample(["Video content", "Educational posts", "Behind-the-scenes content",
                                                    "User-generated content campaigns", "Influencer collaborations", 
                                                    "Interactive stories"], 3),
                    "recommended_strategies": [
                        f"Post {most_common_frequency} focusing on {most_effective_content}",
                        "Engage actively with followers in comments",
                        f"Aim for at least {round(avg_engagement, 1)}% engagement rate",
                        "Develop a consistent visual aesthetic",
                        "Leverage trending hashtags in your niche"
                    ]
                }
            
            result = {
                "competitors": competitor_data,
                "overall_insights": overall_insights
            }
            
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Error analyzing competitors: {e}")
            return json.dumps({"error": str(e)})