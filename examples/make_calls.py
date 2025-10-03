#!/usr/bin/env python3
"""
Example script to initiate outbound calls using the AI agent
"""

import asyncio
from loguru import logger

from src.asterisk.agi_interface import AsteriskAMI
from src.config import settings
from src.utils.logging_config import setup_logging


async def make_outbound_call(phone_number: str, campaign_type: str = "investment"):
    """
    Initiate an outbound call
    
    Args:
        phone_number: Phone number to call (E.164 format recommended)
        campaign_type: Type of campaign (investment, arbitrage, roi)
    """
    logger.info(f"Initiating outbound call to {phone_number}")
    
    # Connect to Asterisk AMI
    ami = AsteriskAMI()
    
    try:
        ami.connect()
        logger.info("Connected to Asterisk AMI")
        
        # Set campaign type as channel variable
        variables = {
            "CAMPAIGN_TYPE": campaign_type,
            "CALL_SOURCE": "automated_campaign"
        }
        
        # Originate the call
        response = ami.originate_call(
            phone_number=phone_number,
            context=settings.asterisk_context,
            extension="s",
            caller_id=settings.asterisk_caller_id,
            variables=variables
        )
        
        logger.info(f"Call initiated: {response}")
        
    except Exception as e:
        logger.error(f"Error initiating call: {e}")
        raise
    
    finally:
        ami.disconnect()


async def make_batch_calls(phone_numbers: list[str], campaign_type: str = "investment"):
    """
    Make multiple outbound calls
    
    Args:
        phone_numbers: List of phone numbers to call
        campaign_type: Type of campaign
    """
    logger.info(f"Starting batch call campaign with {len(phone_numbers)} numbers")
    
    for i, phone_number in enumerate(phone_numbers, 1):
        try:
            logger.info(f"Processing call {i}/{len(phone_numbers)}")
            await make_outbound_call(phone_number, campaign_type)
            
            # Add delay between calls to avoid overwhelming the system
            if i < len(phone_numbers):
                await asyncio.sleep(10)  # 10 seconds between calls
                
        except Exception as e:
            logger.error(f"Error calling {phone_number}: {e}")
            continue


def main():
    """Main entry point"""
    # Setup logging
    setup_logging()
    
    logger.info("=== AIAGC Outbound Calling System ===")
    
    # Example: Single call
    phone_number = "+491234567890"  # Replace with actual number
    
    logger.info(f"Making test call to {phone_number}")
    asyncio.run(make_outbound_call(phone_number, campaign_type="investment"))
    
    # Example: Batch calls
    # phone_numbers = [
    #     "+491234567890",
    #     "+491234567891",
    #     "+491234567892",
    # ]
    # asyncio.run(make_batch_calls(phone_numbers, campaign_type="investment"))


if __name__ == "__main__":
    main()
