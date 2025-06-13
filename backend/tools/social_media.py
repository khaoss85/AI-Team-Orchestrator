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

# 🤖 UNIVERSAL SOCIAL MEDIA PLATFORM CONFIGURATIONS
PLATFORM_CONFIGS = {
    "instagram": {
        "content_types": ["image", "video", "carousel", "story", "reel", "igtv"],
        "optimal_hashtags": 10,
        "character_limits": {"caption": 2200, "bio": 150},
        "posting_times": ["9:00 AM", "6:00 PM", "9:00 PM"],
        "engagement_metrics": ["likes", "comments", "shares", "saves"]
    },
    "twitter": {
        "content_types": ["tweet", "thread", "video", "poll", "space"],
        "optimal_hashtags": 3,
        "character_limits": {"tweet": 280, "bio": 160},
        "posting_times": ["8:00 AM", "12:00 PM", "5:00 PM"],
        "engagement_metrics": ["likes", "retweets", "replies", "clicks"]
    },
    "linkedin": {
        "content_types": ["post", "article", "video", "document", "poll"],
        "optimal_hashtags": 5,
        "character_limits": {"post": 3000, "headline": 220},
        "posting_times": ["8:00 AM", "12:00 PM", "2:00 PM"],
        "engagement_metrics": ["likes", "comments", "shares", "clicks"]
    },
    "tiktok": {
        "content_types": ["video", "live", "duet", "stitch"],
        "optimal_hashtags": 8,
        "character_limits": {"caption": 150, "bio": 80},
        "posting_times": ["6:00 AM", "10:00 AM", "7:00 PM"],
        "engagement_metrics": ["views", "likes", "comments", "shares"]
    },
    "facebook": {
        "content_types": ["post", "photo", "video", "story", "event"],
        "optimal_hashtags": 2,
        "character_limits": {"post": 63206, "bio": 101},
        "posting_times": ["9:00 AM", "1:00 PM", "3:00 PM"],
        "engagement_metrics": ["likes", "comments", "shares", "clicks"]
    },
    "youtube": {
        "content_types": ["video", "short", "live", "premiere"],
        "optimal_hashtags": 15,
        "character_limits": {"title": 100, "description": 5000},
        "posting_times": ["2:00 PM", "8:00 PM", "9:00 PM"],
        "engagement_metrics": ["views", "likes", "comments", "shares", "subscribers"]
    }
}

class UniversalSocialMediaTools:
    """🤖 UNIVERSAL social media tools that work across all platforms"""
    
    @staticmethod
    @function_tool
    async def analyze_hashtags(hashtags: List[str], platform: str = "instagram") -> Dict[str, Any]:
        """
        🤖 UNIVERSAL: Analyze hashtags for any social media platform
        
        Args:
            hashtags: List of hashtags to analyze (without # symbol)
            platform: Target platform (instagram, twitter, linkedin, etc.)
        
        Returns:
            Analysis results with platform-specific insights
        """
        try:
            logger.info(f"Analyzing hashtags for {platform}: {', '.join(hashtags)}")
            
            # Get platform config
            config = PLATFORM_CONFIGS.get(platform.lower(), PLATFORM_CONFIGS["instagram"])
            
            results = {}
            for hashtag in hashtags:
                # Simulate API call delay
                await asyncio.sleep(0.5)
                
                # Generate platform-appropriate stats
                if platform.lower() in ["instagram", "tiktok"]:
                    post_count = random.randint(10000, 10000000)
                    engagement_metric = "engagement_rate"
                elif platform.lower() == "twitter":
                    post_count = random.randint(1000, 1000000)
                    engagement_metric = "tweet_volume"
                elif platform.lower() == "linkedin":
                    post_count = random.randint(100, 100000)
                    engagement_metric = "professional_engagement"
                else:
                    post_count = random.randint(5000, 5000000)
                    engagement_metric = "engagement_rate"
                
                engagement_rate = round(random.uniform(0.5, 8.0), 2)
                growth_rate = round(random.uniform(-2.0, 10.0), 2)
                trending = growth_rate > 3.0
                
                # Generate platform-specific related tags
                if platform.lower() == "linkedin":
                    related_pool = ["business", "professional", "career", "leadership", "innovation", "industry"]
                elif platform.lower() == "tiktok":
                    related_pool = ["viral", "trending", "fyp", "foryou", "dance", "comedy"]
                elif platform.lower() == "twitter":
                    related_pool = ["trending", "breaking", "news", "opinion", "thread", "viral"]
                else:
                    related_pool = ["trending", "viral", "popular", "community", "content", "creator"]
                
                related_tags = random.sample(related_pool, min(5, len(related_pool)))
                
                results[hashtag] = {
                    "posts_count": post_count,
                    engagement_metric: f"{engagement_rate}%",
                    "growth_rate": f"{growth_rate}%",
                    "trending": trending,
                    "popularity_score": round(min(post_count / 1000000, 1) * 10, 1),
                    "related_tags": related_tags,
                    "best_posting_times": config["posting_times"],
                    "platform_specific": {
                        "optimal_hashtag_count": config["optimal_hashtags"],
                        "character_limits": config["character_limits"]
                    }
                }
            
            # Add platform-specific analysis
            if hashtags:
                top_hashtag = max(hashtags, key=lambda h: results[h]["popularity_score"])
                trending_hashtags = [h for h in hashtags if results[h]["trending"]]
                
                results["analysis"] = {
                    "platform": platform,
                    "top_performing_hashtag": top_hashtag,
                    "trending_hashtags": trending_hashtags,
                    "recommendation": f"Use a mix of popular and niche hashtags optimized for {platform}",
                    "platform_tips": UniversalSocialMediaTools._get_platform_tips(platform)
                }
            
            return results
        except Exception as e:
            logger.error(f"Error analyzing hashtags for {platform}: {e}")
            return {"error": str(e)}
    
    @staticmethod
    @function_tool
    async def analyze_account(username: str, platform: str = "instagram") -> Dict[str, Any]:
        """
        🤖 UNIVERSAL: Analyze social media account across platforms
        
        Args:
            username: Account username/handle
            platform: Target platform
        
        Returns:
            Account analysis with platform-specific metrics
        """
        try:
            logger.info(f"Analyzing {platform} account: {username}")
            
            # Get platform config
            config = PLATFORM_CONFIGS.get(platform.lower(), PLATFORM_CONFIGS["instagram"])
            
            # Simulate API call delay
            await asyncio.sleep(1)
            
            # Generate platform-appropriate stats
            if platform.lower() == "youtube":
                followers_label = "subscribers"
                followers = random.randint(100, 10000000)
                posts_label = "videos"
                posts = random.randint(10, 1000)
            elif platform.lower() == "twitter":
                followers_label = "followers"
                followers = random.randint(100, 5000000)
                posts_label = "tweets"
                posts = random.randint(100, 50000)
            elif platform.lower() == "linkedin":
                followers_label = "connections"
                followers = random.randint(50, 30000)
                posts_label = "posts"
                posts = random.randint(10, 500)
            else:
                followers_label = "followers"
                followers = random.randint(100, 1000000)
                posts_label = "posts"
                posts = random.randint(10, 1000)
            
            following = random.randint(100, 5000)
            engagement_rate = round(random.uniform(0.5, 8.0), 2)
            
            # Generate platform-specific content distribution
            content_types = config["content_types"]
            post_distribution = {}
            for content_type in content_types:
                post_distribution[content_type] = round(random.uniform(10, 60), 1)
            
            # Normalize to 100%
            total = sum(post_distribution.values())
            for key in post_distribution:
                post_distribution[key] = round((post_distribution[key] / total) * 100, 1)
            
            posting_frequency = random.choice(["daily", "2-3 times per week", "weekly", "bi-weekly"])
            
            # Create platform-specific analysis
            account_info = {
                "platform": platform,
                "username": username,
                f"{followers_label}_count": followers,
                "following_count": following,
                f"{posts_label}_count": posts,
                "engagement_rate": f"{engagement_rate}%",
                "content_distribution": post_distribution,
                "posting_frequency": posting_frequency,
                "best_performing_content": {
                    "type": random.choice(content_types),
                    "average_engagement": int(followers * random.uniform(0.02, 0.1)),
                    "engagement_metrics": config["engagement_metrics"]
                },
                "growth_trend": random.choice(["increasing", "stable", "decreasing"]),
                "platform_insights": {
                    "optimal_posting_times": config["posting_times"],
                    "recommended_content_types": content_types[:3],
                    "character_limits": config["character_limits"]
                }
            }
            
            return account_info
        except Exception as e:
            logger.error(f"Error analyzing {platform} account: {e}")
            return {"error": str(e)}
    
    @staticmethod
    @function_tool
    async def generate_content_ideas(
        topic: str, 
        target_audience: str, 
        platform: str = "instagram",
        count: int = 5,
        content_type: str = "post"
    ) -> List[Dict[str, Any]]:
        """
        🤖 UNIVERSAL: Generate content ideas for any social media platform
        
        Args:
            topic: Main topic or niche
            target_audience: Description of target audience
            platform: Target platform
            count: Number of ideas to generate
            content_type: Type of content (post, video, story, etc.)
        
        Returns:
            List of platform-optimized content ideas
        """
        try:
            logger.info(f"Generating {count} {content_type} ideas for {platform}: topic={topic}")
            
            # Get platform config
            config = PLATFORM_CONFIGS.get(platform.lower(), PLATFORM_CONFIGS["instagram"])
            
            # Simulate thinking time
            await asyncio.sleep(1.5)
            
            ideas = []
            for i in range(count):
                # Use platform-appropriate content types
                if content_type == "auto":
                    selected_type = random.choice(config["content_types"])
                else:
                    selected_type = content_type if content_type in config["content_types"] else config["content_types"][0]
                
                # Generate universal themes (not domain-specific)
                universal_themes = [
                    "How-to guide", "Behind the scenes", "Tips and tricks", "Case study",
                    "Q&A session", "Day in the life", "Before and after", "Tutorial",
                    "Industry insights", "Personal story", "Trending topic", "Educational content"
                ]
                theme = random.choice(universal_themes)
                
                # Generate platform-appropriate hashtags
                hashtags = [f"#{topic.lower()}", f"#{platform.lower()}"]
                
                # Add platform-specific hashtags
                if platform.lower() == "linkedin":
                    hashtags.extend(["#professional", "#business", "#career"])
                elif platform.lower() == "tiktok":
                    hashtags.extend(["#fyp", "#viral", "#trending"])
                elif platform.lower() == "twitter":
                    hashtags.extend(["#thread", "#discussion"])
                else:
                    hashtags.extend(["#content", "#community"])
                
                # Limit hashtags based on platform optimal count
                hashtags = hashtags[:config["optimal_hashtags"]]
                
                # Build platform-optimized idea
                idea = {
                    "title": f"{theme} {selected_type}",
                    "description": f"Create a {selected_type.lower()} about {theme.lower()} for {target_audience} on {platform}",
                    "platform": platform,
                    "content_type": selected_type,
                    "theme": theme,
                    "hashtags": hashtags,
                    "estimated_engagement": f"{random.randint(1, 5)}/5",
                    "best_posting_time": random.choice(config["posting_times"]),
                    "platform_optimization": {
                        "character_limits": config["character_limits"],
                        "engagement_tactics": UniversalSocialMediaTools._get_platform_tactics(platform),
                        "content_format": UniversalSocialMediaTools._get_format_guidelines(platform, selected_type)
                    }
                }
                
                ideas.append(idea)
            
            return ideas
        except Exception as e:
            logger.error(f"Error generating content ideas for {platform}: {e}")
            return [{"error": str(e)}]
    
    @staticmethod
    def _get_platform_tips(platform: str) -> List[str]:
        """Get platform-specific optimization tips"""
        tips = {
            "instagram": [
                "Use Stories to increase engagement",
                "Post consistently at optimal times",
                "Mix content types (photos, videos, carousels)"
            ],
            "twitter": [
                "Keep tweets concise and engaging",
                "Use threads for longer content",
                "Engage with trending hashtags"
            ],
            "linkedin": [
                "Share professional insights",
                "Use native video for better reach",
                "Engage with industry discussions"
            ],
            "tiktok": [
                "Follow trending sounds and challenges",
                "Keep videos under 60 seconds",
                "Use trending hashtags strategically"
            ]
        }
        return tips.get(platform.lower(), ["Post consistently", "Engage with your audience", "Use relevant hashtags"])
    
    @staticmethod
    def _get_platform_tactics(platform: str) -> List[str]:
        """Get platform-specific engagement tactics"""
        tactics = {
            "instagram": ["Use polls in Stories", "Ask questions in captions", "Share user-generated content"],
            "twitter": ["Create Twitter polls", "Start conversations", "Share quick tips"],
            "linkedin": ["Ask thought-provoking questions", "Share industry insights", "Comment on others' posts"],
            "tiktok": ["Use trending sounds", "Create duets/stitches", "Jump on challenges"]
        }
        return tactics.get(platform.lower(), ["Engage authentically", "Post consistently", "Use relevant hashtags"])
    
    @staticmethod
    def _get_format_guidelines(platform: str, content_type: str) -> Dict[str, Any]:
        """Get format guidelines for specific platform and content type"""
        guidelines = {
            "visual_specs": "High-quality, well-lit images/videos",
            "text_overlay": "Keep text readable and minimal",
            "call_to_action": "Include clear next steps"
        }
        
        # Add platform-specific guidelines
        if platform.lower() == "instagram" and content_type == "reel":
            guidelines.update({
                "duration": "15-30 seconds",
                "orientation": "vertical",
                "trending_audio": "Use popular sounds"
            })
        elif platform.lower() == "linkedin" and content_type == "article":
            guidelines.update({
                "length": "1000-2000 words",
                "format": "Professional tone",
                "structure": "Clear headers and bullet points"
            })
        
        return guidelines

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
    async def generate_content_ideas(topic: str, target_audience: str, count: Optional[int] = None) -> str:
        """
        Generate content ideas for Instagram based on topic and target audience.
        
        Args:
            topic: The main topic or niche (e.g., "fitness", "fashion")
            target_audience: Description of the target audience (e.g., "young adults interested in sustainable fashion")
            count: Number of ideas to generate
            
        Returns:
            List of content ideas with details as JSON string
        """
        actual_count = count if count is not None and count > 0 else 5
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
            for i in range(actual_count):
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