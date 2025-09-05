#!/usr/bin/env python3
"""
OpenAI Usage API Client Service
Fetches real usage data from OpenAI's /v1/usage endpoint for accurate cost tracking
"""

import asyncio
import calendar
import logging
import os
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field
from enum import Enum
import httpx
import json
from collections import defaultdict

logger = logging.getLogger(__name__)

class AggregationLevel(str, Enum):
    """Time aggregation levels for usage data"""
    DAILY = "day"
    HOURLY = "hour" 
    MINUTE = "minute"

@dataclass
class UsageDataPoint:
    """Single usage data point from API"""
    date: datetime
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    requests_count: int
    project_id: Optional[str] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'UsageDataPoint':
        """Create from API response data - handles both old and new formats"""
        # Handle new format with aggregation_timestamp (Unix timestamp)
        if 'aggregation_timestamp' in data:
            # New format from Usage API
            timestamp = data['aggregation_timestamp']
            date = datetime.fromtimestamp(timestamp)
            
            # Model is in snapshot_id field (e.g., "gpt-4o-2024-08-06")
            model = data.get('snapshot_id', 'unknown')
            
            # Token counts have different field names
            input_tokens = data.get('n_context_tokens_total', 0)
            output_tokens = data.get('n_generated_tokens_total', 0)
            total_tokens = input_tokens + output_tokens
            
            # Calculate costs based on model and token counts
            # These are approximate costs - adjust based on your pricing
            input_cost = 0.0
            output_cost = 0.0
            
            # Model pricing (approximate - update with actual pricing)
            if 'gpt-4o' in model.lower():
                input_cost = (input_tokens / 1000) * 0.005  # $5 per 1M input tokens
                output_cost = (output_tokens / 1000) * 0.015  # $15 per 1M output tokens
            elif 'gpt-4' in model.lower():
                input_cost = (input_tokens / 1000) * 0.03  # $30 per 1M input tokens
                output_cost = (output_tokens / 1000) * 0.06  # $60 per 1M output tokens
            elif 'gpt-3.5' in model.lower():
                input_cost = (input_tokens / 1000) * 0.0005  # $0.50 per 1M input tokens
                output_cost = (output_tokens / 1000) * 0.0015  # $1.50 per 1M output tokens
            else:
                # Default pricing for unknown models
                input_cost = (input_tokens / 1000) * 0.001
                output_cost = (output_tokens / 1000) * 0.002
                
            total_cost = input_cost + output_cost
            
            return cls(
                date=date,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                input_cost=input_cost,
                output_cost=output_cost,
                total_cost=total_cost,
                requests_count=data.get('n_requests', 1),
                project_id=data.get('project_id')
            )
        else:
            # Old format (fallback)
            return cls(
                date=datetime.fromisoformat(data['date'].replace('Z', '+00:00')),
                model=data.get('model', 'unknown'),
                input_tokens=data.get('input_tokens', 0),
                output_tokens=data.get('output_tokens', 0),
                total_tokens=data.get('total_tokens', 0),
                input_cost=data.get('input_cost', 0.0),
                output_cost=data.get('output_cost', 0.0),
                total_cost=data.get('total_cost', 0.0),
                requests_count=data.get('n_requests', 1),
                project_id=data.get('project_id')
            )

@dataclass
class UsageSummary:
    """Aggregated usage summary"""
    start_date: datetime
    end_date: datetime
    total_tokens: int = 0
    total_cost: float = 0.0
    total_requests: int = 0
    model_breakdown: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    daily_breakdown: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    hourly_breakdown: Optional[Dict[str, Dict[str, Any]]] = field(default_factory=dict)
    
    def add_data_point(self, point: UsageDataPoint):
        """Add a data point to the summary"""
        self.total_tokens += point.total_tokens
        self.total_cost += point.total_cost
        self.total_requests += point.requests_count
        
        # Update model breakdown
        if point.model not in self.model_breakdown:
            self.model_breakdown[point.model] = {
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0,
                'input_cost': 0.0,
                'output_cost': 0.0,
                'total_cost': 0.0,
                'requests_count': 0
            }
        
        model_stats = self.model_breakdown[point.model]
        model_stats['input_tokens'] += point.input_tokens
        model_stats['output_tokens'] += point.output_tokens
        model_stats['total_tokens'] += point.total_tokens
        model_stats['input_cost'] += point.input_cost
        model_stats['output_cost'] += point.output_cost
        model_stats['total_cost'] += point.total_cost
        model_stats['requests_count'] += point.requests_count
        
        # Update daily breakdown
        day_key = point.date.strftime('%Y-%m-%d')
        if day_key not in self.daily_breakdown:
            self.daily_breakdown[day_key] = {
                'date': day_key,
                'total_tokens': 0,
                'total_cost': 0.0,
                'requests_count': 0,
                'models': defaultdict(lambda: {'tokens': 0, 'cost': 0.0, 'requests': 0})
            }
        
        day_stats = self.daily_breakdown[day_key]
        day_stats['total_tokens'] += point.total_tokens
        day_stats['total_cost'] += point.total_cost
        day_stats['requests_count'] += point.requests_count
        day_stats['models'][point.model]['tokens'] += point.total_tokens
        day_stats['models'][point.model]['cost'] += point.total_cost
        day_stats['models'][point.model]['requests'] += point.requests_count
        
        # Update hourly breakdown if enabled
        if self.hourly_breakdown is not None:
            hour_key = point.date.strftime('%Y-%m-%d %H:00')
            if hour_key not in self.hourly_breakdown:
                self.hourly_breakdown[hour_key] = {
                    'hour': hour_key,
                    'total_tokens': 0,
                    'total_cost': 0.0,
                    'requests_count': 0
                }
            
            hour_stats = self.hourly_breakdown[hour_key]
            hour_stats['total_tokens'] += point.total_tokens
            hour_stats['total_cost'] += point.total_cost
            hour_stats['requests_count'] += point.requests_count

class OpenAIUsageAPIClient:
    """
    Client for OpenAI Usage API v1
    Fetches real usage data for accurate cost tracking
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required for usage tracking")
        
        self.base_url = "https://api.openai.com/v1"
        self.usage_endpoint = f"{self.base_url}/usage"
        
        # Cache for recent usage data
        self.usage_cache: Dict[str, UsageSummary] = {}
        self.cache_ttl_seconds = int(os.getenv('USAGE_CACHE_TTL_SECONDS', '300'))  # 5 minutes default
        self.last_cache_update: Optional[datetime] = None
        
        # Rate limiting for API calls
        self.min_request_interval = int(os.getenv('USAGE_API_MIN_INTERVAL_SECONDS', '10'))
        self.last_request_time: Optional[datetime] = None
        
        logger.info("🔌 OpenAI Usage API Client initialized")
    
    async def fetch_usage(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        aggregation: AggregationLevel = AggregationLevel.DAILY,
        model: Optional[str] = None,
        project_id: Optional[str] = None,
        use_cache: bool = True
    ) -> UsageSummary:
        """
        Fetch usage data from OpenAI Usage API
        
        Args:
            start_date: Start of period (defaults to 7 days ago)
            end_date: End of period (defaults to today)
            aggregation: Time aggregation level (day/hour/minute)
            model: Filter by specific model
            project_id: Filter by project ID
            use_cache: Use cached data if available and fresh
            
        Returns:
            UsageSummary with real usage data
        """
        try:
            # Default date range
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=7)
            
            # Check cache if enabled
            cache_key = f"{start_date.date()}_{end_date.date()}_{aggregation}_{model}_{project_id}"
            if use_cache and cache_key in self.usage_cache:
                if self.last_cache_update:
                    cache_age = (datetime.now() - self.last_cache_update).total_seconds()
                    if cache_age < self.cache_ttl_seconds:
                        logger.info(f"📋 Returning cached usage data (age: {cache_age:.0f}s)")
                        return self.usage_cache[cache_key]
            
            # Rate limiting
            if self.last_request_time:
                time_since_last = (datetime.now() - self.last_request_time).total_seconds()
                if time_since_last < self.min_request_interval:
                    wait_time = self.min_request_interval - time_since_last
                    logger.info(f"⏳ Rate limiting: waiting {wait_time:.1f}s before next request")
                    await asyncio.sleep(wait_time)
            
            # Build query parameters
            # OpenAI API requires 'date' for single day, 'start_date'/'end_date' for ranges
            params = {}
            
            # Check if it's a single day query
            if start_date.date() == end_date.date():
                # Single day - use 'date' parameter
                params['date'] = start_date.date().isoformat()
            else:
                # Date range - use 'start_date' and 'end_date'
                params['start_date'] = start_date.date().isoformat()
                params['end_date'] = end_date.date().isoformat()
            
            params['bucket_width'] = aggregation.value
            
            if model:
                params['model'] = model
            if project_id:
                params['project_id'] = project_id
            
            # Make API request
            logger.info(f"📡 Fetching usage data from OpenAI API: {params}")
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.usage_endpoint,
                    headers={
                        'Authorization': f'Bearer {self.api_key}',
                        'Content-Type': 'application/json'
                    },
                    params=params,
                    timeout=30.0
                )
                
                self.last_request_time = datetime.now()
                
                if response.status_code != 200:
                    error_msg = f"Usage API error: {response.status_code}"
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('error', {}).get('message', response.text)
                        error_msg = f"{error_msg} - {error_detail}"
                    except:
                        error_msg = f"{error_msg} - {response.text}"
                    
                    logger.error(f"❌ {error_msg}")
                    
                    # Provide helpful feedback for common errors
                    if response.status_code == 400 and "Missing query parameter" in error_msg:
                        logger.info("💡 Hint: API parameter issue detected. Using fallback empty summary.")
                    elif response.status_code == 401:
                        logger.error("🔑 Authentication failed. Check your OPENAI_API_KEY.")
                    elif response.status_code == 429:
                        logger.warning("⏳ Rate limited on Usage API. Will retry with cached data.")
                    
                    return self._create_empty_summary(start_date, end_date)
                
                data = response.json()
                
            # Parse response and create summary
            summary = UsageSummary(
                start_date=start_date,
                end_date=end_date,
                hourly_breakdown={} if aggregation == AggregationLevel.HOURLY else None
            )
            
            # Process usage data points
            usage_data = data.get('data', [])
            if not usage_data and 'buckets' in data:
                # Alternative format with buckets
                usage_data = data.get('buckets', [])
            
            for item in usage_data:
                try:
                    point = UsageDataPoint.from_api_response(item)
                    summary.add_data_point(point)
                except KeyError as e:
                    logger.warning(f"Failed to parse usage data point - missing key: {e}")
                    # Log the structure for debugging (only once)
                    if summary.total_requests == 0:
                        logger.debug(f"Data point structure: {list(item.keys()) if isinstance(item, dict) else type(item)}")
                    continue
                except Exception as e:
                    logger.warning(f"Failed to parse usage data point: {e}")
                    continue
            
            # Update cache
            self.usage_cache[cache_key] = summary
            self.last_cache_update = datetime.now()
            
            logger.info(f"✅ Fetched usage data: ${summary.total_cost:.2f} across {summary.total_requests} requests")
            return summary
            
        except httpx.RequestError as e:
            logger.error(f"❌ Network error fetching usage data: {e}")
            return self._create_empty_summary(start_date, end_date)
        except Exception as e:
            logger.error(f"❌ Unexpected error in usage API: {e}")
            return self._create_empty_summary(start_date, end_date)
    
    async def get_current_month_usage(self) -> UsageSummary:
        """Get usage for current billing month"""
        today = datetime.now()
        start_of_month = datetime(today.year, today.month, 1)
        
        # The API doesn't support date ranges anymore, we need to fetch each day
        # and aggregate them
        monthly_summary = UsageSummary(
            start_date=start_of_month,
            end_date=today
        )
        
        # Iterate through each day of the month
        current_date = start_of_month
        while current_date.date() <= today.date():
            try:
                # Fetch usage for single day
                day_summary = await self.fetch_usage(
                    start_date=current_date,
                    end_date=current_date,
                    aggregation=AggregationLevel.DAILY,
                    use_cache=True
                )
                
                # Aggregate the day's data into monthly summary
                monthly_summary.total_cost += day_summary.total_cost
                monthly_summary.total_tokens += day_summary.total_tokens
                monthly_summary.total_requests += day_summary.total_requests
                
                # Merge model breakdown
                for model, stats in day_summary.model_breakdown.items():
                    if model not in monthly_summary.model_breakdown:
                        monthly_summary.model_breakdown[model] = {
                            'input_tokens': 0,
                            'output_tokens': 0,
                            'total_tokens': 0,
                            'input_cost': 0.0,
                            'output_cost': 0.0,
                            'total_cost': 0.0,
                            'requests_count': 0
                        }
                    
                    model_stats = monthly_summary.model_breakdown[model]
                    model_stats['input_tokens'] += stats.get('input_tokens', 0)
                    model_stats['output_tokens'] += stats.get('output_tokens', 0)
                    model_stats['total_tokens'] += stats.get('total_tokens', 0)
                    model_stats['input_cost'] += stats.get('input_cost', 0)
                    model_stats['output_cost'] += stats.get('output_cost', 0)
                    model_stats['total_cost'] += stats.get('total_cost', 0)
                    model_stats['requests_count'] += stats.get('requests_count', 0)
                
                # Add daily breakdown
                day_key = current_date.strftime('%Y-%m-%d')
                monthly_summary.daily_breakdown[day_key] = {
                    'date': day_key,
                    'cost': day_summary.total_cost,
                    'tokens': day_summary.total_tokens,
                    'requests': day_summary.total_requests
                }
                
            except Exception as e:
                logger.warning(f"Failed to fetch usage for {current_date.date()}: {e}")
            
            # Move to next day
            current_date += timedelta(days=1)
        
        logger.info(f"✅ Aggregated monthly usage: ${monthly_summary.total_cost:.2f}")
        return monthly_summary
    
    async def get_today_usage(self) -> UsageSummary:
        """Get usage for today"""
        today = datetime.now()
        start_of_day = datetime(today.year, today.month, today.day)
        # End of day should be just before midnight
        end_of_day = datetime(today.year, today.month, today.day, 23, 59, 59)
        return await self.fetch_usage(
            start_date=start_of_day,
            end_date=end_of_day,
            aggregation=AggregationLevel.HOURLY
        )
    
    async def get_model_comparison(
        self,
        days: int = 7
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compare usage across different models
        
        Returns:
            Dictionary with model comparison data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        summary = await self.fetch_usage(
            start_date=start_date,
            end_date=end_date,
            aggregation=AggregationLevel.DAILY
        )
        
        # Calculate model efficiency metrics
        comparison = {}
        for model, stats in summary.model_breakdown.items():
            avg_tokens_per_request = (
                stats['total_tokens'] / stats['requests_count'] 
                if stats['requests_count'] > 0 else 0
            )
            cost_per_1k_tokens = (
                (stats['total_cost'] / stats['total_tokens']) * 1000 
                if stats['total_tokens'] > 0 else 0
            )
            
            comparison[model] = {
                'total_cost': stats['total_cost'],
                'total_tokens': stats['total_tokens'],
                'total_requests': stats['requests_count'],
                'avg_tokens_per_request': avg_tokens_per_request,
                'cost_per_1k_tokens': cost_per_1k_tokens,
                'cost_percentage': (
                    (stats['total_cost'] / summary.total_cost) * 100 
                    if summary.total_cost > 0 else 0
                )
            }
        
        return comparison
    
    async def get_cost_trend(
        self,
        days: int = 30
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get cost trend over specified period
        
        Returns:
            Dictionary with daily and cumulative cost trends
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        summary = await self.fetch_usage(
            start_date=start_date,
            end_date=end_date,
            aggregation=AggregationLevel.DAILY
        )
        
        # Create trend data
        daily_trend = []
        cumulative_cost = 0.0
        cumulative_trend = []
        
        # Sort days chronologically
        for day in sorted(summary.daily_breakdown.keys()):
            day_data = summary.daily_breakdown[day]
            
            daily_trend.append({
                'date': day,
                'cost': day_data['total_cost'],
                'tokens': day_data['total_tokens'],
                'requests': day_data['requests_count']
            })
            
            cumulative_cost += day_data['total_cost']
            cumulative_trend.append({
                'date': day,
                'cumulative_cost': cumulative_cost
            })
        
        return {
            'daily': daily_trend,
            'cumulative': cumulative_trend,
            'total_cost': summary.total_cost,
            'avg_daily_cost': summary.total_cost / days if days > 0 else 0
        }
    
    async def check_budget_status(
        self,
        monthly_budget: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Check current month's usage against budget
        
        Args:
            monthly_budget: Monthly budget in USD (uses env var if not provided)
            
        Returns:
            Budget status with projections
        """
        if not monthly_budget:
            monthly_budget = float(os.getenv('OPENAI_MONTHLY_BUDGET_USD', '100'))
        
        # Get current month usage
        usage = await self.get_current_month_usage()
        
        # Calculate days in month and days elapsed
        today = datetime.now()
        # Calculate actual days in current month
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        days_elapsed = today.day
        days_remaining = days_in_month - days_elapsed
        
        # Calculate projections
        current_spend = usage.total_cost
        daily_average = current_spend / days_elapsed if days_elapsed > 0 else 0
        projected_monthly = daily_average * days_in_month
        
        # Budget analysis
        budget_used_percent = (current_spend / monthly_budget) * 100 if monthly_budget > 0 else 0
        projected_overage = max(0, projected_monthly - monthly_budget)
        
        status = "normal"
        if budget_used_percent > 90:
            status = "critical"
        elif budget_used_percent > 75:
            status = "warning"
        elif projected_monthly > monthly_budget:
            status = "caution"
        
        return {
            'status': status,
            'monthly_budget': monthly_budget,
            'current_spend': current_spend,
            'budget_used_percent': budget_used_percent,
            'daily_average': daily_average,
            'projected_monthly': projected_monthly,
            'projected_overage': projected_overage,
            'days_remaining': days_remaining,
            'recommended_daily_limit': (monthly_budget - current_spend) / days_remaining if days_remaining > 0 else 0,
            'models_breakdown': usage.model_breakdown
        }
    
    def _create_empty_summary(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> UsageSummary:
        """Create empty summary for fallback"""
        return UsageSummary(
            start_date=start_date,
            end_date=end_date
        )
    
    def clear_cache(self):
        """Clear usage data cache"""
        self.usage_cache.clear()
        self.last_cache_update = None
        logger.info("🧹 Usage cache cleared")


# Global client instance
_usage_client: Optional[OpenAIUsageAPIClient] = None

def get_usage_client() -> OpenAIUsageAPIClient:
    """Get or create global usage API client"""
    global _usage_client
    if not _usage_client:
        try:
            _usage_client = OpenAIUsageAPIClient()
        except ValueError as e:
            logger.error(f"Failed to initialize usage client: {e}")
            raise
    return _usage_client


async def test_usage_api():
    """Test the usage API client"""
    try:
        client = get_usage_client()
        
        # Test different queries
        print("📊 Testing OpenAI Usage API Client\n")
        
        # Today's usage
        print("Today's Usage:")
        today_usage = await client.get_today_usage()
        print(f"  Total Cost: ${today_usage.total_cost:.4f}")
        print(f"  Total Tokens: {today_usage.total_tokens:,}")
        print(f"  Total Requests: {today_usage.total_requests}")
        print()
        
        # Current month usage
        print("Current Month Usage:")
        month_usage = await client.get_current_month_usage()
        print(f"  Total Cost: ${month_usage.total_cost:.2f}")
        print(f"  Total Tokens: {month_usage.total_tokens:,}")
        for model, stats in month_usage.model_breakdown.items():
            print(f"  {model}: ${stats['total_cost']:.2f} ({stats['requests_count']} requests)")
        print()
        
        # Budget status
        print("Budget Status:")
        budget_status = await client.check_budget_status()
        print(f"  Status: {budget_status['status'].upper()}")
        print(f"  Current Spend: ${budget_status['current_spend']:.2f} / ${budget_status['monthly_budget']:.2f}")
        print(f"  Budget Used: {budget_status['budget_used_percent']:.1f}%")
        print(f"  Projected Monthly: ${budget_status['projected_monthly']:.2f}")
        if budget_status['projected_overage'] > 0:
            print(f"  ⚠️ Projected Overage: ${budget_status['projected_overage']:.2f}")
        print()
        
        # Model comparison
        print("Model Comparison (Last 7 Days):")
        comparison = await client.get_model_comparison()
        for model, data in comparison.items():
            print(f"  {model}:")
            print(f"    Cost: ${data['total_cost']:.2f} ({data['cost_percentage']:.1f}%)")
            print(f"    Cost per 1K tokens: ${data['cost_per_1k_tokens']:.4f}")
        
    except Exception as e:
        print(f"❌ Error testing usage API: {e}")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_usage_api())