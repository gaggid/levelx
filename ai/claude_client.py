import anthropic
from typing import Dict, List, Optional
from config.settings import settings
import logging
import time
from anthropic import APIError, APIConnectionError, RateLimitError

logger = logging.getLogger(__name__)


class ClaudeAPIError(Exception):
    """Custom exception for Claude API errors"""
    pass


class ClaudeClient:
    """
    Wrapper for Anthropic Claude API
    """
    
    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ClaudeAPIError("ANTHROPIC_API_KEY not found in settings")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"  # Latest Sonnet model
        self.max_tokens = 2000  # Cost control
        self.timeout = 60
        self.max_retries = 3
        
        logger.info(f"ClaudeClient initialized with model: {self.model}")
    
    def _make_request(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: float = 1.0,
        retry_count: int = 0,
        cost_tracker=None  # Add parameter
    ) -> str:
        """Make request to Claude API with retry logic"""
        try:
            logger.info(f"Making Claude API request (attempt {retry_count + 1})")
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=temperature,
                system=system if system else anthropic.NOT_GIVEN,
                messages=messages
            )
            
            # Extract text
            text = response.content[0].text
            
            # Log token usage
            logger.info(
                f"Claude response received. "
                f"Input tokens: {response.usage.input_tokens}, "
                f"Output tokens: {response.usage.output_tokens}"
            )
            
            # Track cost
            if cost_tracker:
                cost_tracker.add_claude_call(
                    response.usage.input_tokens,
                    response.usage.output_tokens
                )
            
            return text
            
        except RateLimitError as e:
            logger.warning(f"Rate limit hit: {e}")
            if retry_count < self.max_retries:
                wait_time = 2 ** retry_count  # Exponential backoff
                logger.info(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                return self._make_request(messages, system, temperature, retry_count + 1)
            else:
                raise ClaudeAPIError("Rate limit exceeded after retries")
        
        except APIConnectionError as e:
            logger.error(f"Connection error: {e}")
            if retry_count < self.max_retries:
                time.sleep(2)
                return self._make_request(messages, system, temperature, retry_count + 1)
            else:
                raise ClaudeAPIError(f"Connection failed: {str(e)}")
        
        except APIError as e:
            logger.error(f"Claude API error: {e}")
            raise ClaudeAPIError(f"API error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise ClaudeAPIError(f"Unexpected error: {str(e)}")
    
    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 1.0,
        cost_tracker=None  # Add parameter
    ) -> str:
        """Simple completion"""
        messages = [{"role": "user", "content": prompt}]
        return self._make_request(messages, system, temperature, 0, cost_tracker)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: float = 1.0
    ) -> str:
        """
        Multi-turn conversation
        
        Args:
            messages: Conversation history
            system: Optional system prompt
            temperature: Sampling temperature
        
        Returns:
            Claude's response
        """
        return self._make_request(messages, system, temperature)


# Test function
def test_client():
    """Test Claude API client"""
    try:
        print("\n🧪 Testing Claude API Client\n")
        
        client = ClaudeClient()
        
        # Test 1: Simple completion
        print("1️⃣ Testing simple completion...")
        response = client.complete(
            prompt="Say 'Hello from Claude!' and nothing else.",
            temperature=0
        )
        print(f"   Response: {response}")
        assert "hello" in response.lower() and "claude" in response.lower()
        print("   ✅ Simple completion works!\n")
        
        # Test 2: System prompt
        print("2️⃣ Testing with system prompt...")
        response = client.complete(
            prompt="What's 2+2?",
            system="You are a helpful math tutor. Always show your work.",
            temperature=0
        )
        print(f"   Response: {response[:100]}...")
        assert "4" in response
        print("   ✅ System prompt works!\n")
        
        # Test 3: Multi-turn chat
        print("3️⃣ Testing multi-turn chat...")
        messages = [
            {"role": "user", "content": "My name is Alice."},
            {"role": "assistant", "content": "Nice to meet you, Alice!"},
            {"role": "user", "content": "What's my name?"}
        ]
        response = client.chat(messages, temperature=0)
        print(f"   Response: {response}")
        assert "alice" in response.lower()
        print("   ✅ Multi-turn chat works!\n")
        
        print("🎉 All tests passed!")
        print("\n💰 Cost estimate for these tests: ~$0.01")
        
    except ClaudeAPIError as e:
        print(f"\n❌ Test failed: {e}")
        print("\n⚠️ Make sure ANTHROPIC_API_KEY is set in your .env file")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    test_client()