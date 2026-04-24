#!/usr/bin/env python3
"""Debug script to test OpenRouter API connectivity"""
import asyncio
import httpx
from app.path_ai.core.config import settings

async def test_openrouter():
    print(f"Base URL: {settings.openrouter_base_url}")
    print(f"Model: {settings.model_name}")
    print(f"API Key: {settings.openrouter_api_key[:10]}...")

    async with httpx.AsyncClient(
        base_url=settings.openrouter_base_url,
        headers={
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    ) as client:
        # First, check available models
        print("\nChecking available models...")
        try:
            models_response = await client.get("/models")
            print(f"Models status: {models_response.status_code}")
            if models_response.status_code == 200:
                models_data = models_response.json()
                print(f"Total models available: {len(models_data.get('data', []))}")
                # Print some free models
                free_models = [m for m in models_data.get('data', []) if ':free' in m.get('id', '')]
                print(f"\nFree models available: {len(free_models)}")
                for m in free_models[:15]:
                    print(f"  - {m['id']}")

                # Check for phi models
                phi_models = [m for m in models_data.get('data', []) if 'phi' in m.get('id', '').lower()]
                if phi_models:
                    print(f"\nPhi models available: {len(phi_models)}")
                    for m in phi_models[:10]:
                        print(f"  - {m['id']}")
                else:
                    print("\nNo phi models found.")

                # Check for gpt-oss model
                gpt_oss_models = [m for m in models_data.get('data', []) if 'gpt-oss' in m.get('id', '').lower()]
                if gpt_oss_models:
                    print(f"\nGPT-OSS models available: {len(gpt_oss_models)}")
                    for m in gpt_oss_models:
                        print(f"  - {m['id']}")
                else:
                    print("\nNo gpt-oss models found.")
            else:
                print(f"Models response: {models_response.text[:500]}")
        except Exception as e:
            print(f"Error fetching models: {e}")

        # Then test chat completion
        print("\nMaking test request to /chat/completions...")
        payload = {
            "model": settings.model_name,
            "messages": [{"role": "user", "content": "Hello"}],
            "temperature": 0.7,
            "max_tokens": 10,
        }
        try:
            response = await client.post("/chat/completions", json=payload)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_openrouter())
