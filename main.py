from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
from io import BytesIO
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
BOT_USERNAME = "@banana16_bot"

def configure_model():
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    return genai.GenerativeModel("gemini-1.5-flash")

def build_food_prompt(image_description):
    prompt = f"""
    You are a food analysis assistant. Given the description of the food in the image, provide the following information:
    1. Food name
    2. Calories (per typical serving)
    3. Main ingredients
    4. Nutritional breakdown (protein, carbs, fats, etc.)
    
    Image Description:
    {image_description}

    Please just reply short simple and concise. If the information is not available, just make an estimate.
    
    Reply in telegram markdown format:
    *bold \*text*
    _italic \*text_
    __underline__
    ~strikethrough~
    *bold _italic bold ~italic bold strikethrough~ __underline italic bold___ bold*
    [inline URL](http://www.example.com/)
    [inline mention of a user](tg://user?id=123456789)
    `inline fixed-width code`
    ```
    pre-formatted fixed-width code block
    ```
    ```python
    pre-formatted fixed-width code block written in the Python programming language
    ```
    Do not add double next lines. Just one is enough \n.

    IMPORTANT: please add preceeding \ to the reserved entities which are _*[]()~`>#+-=|.! and curly braces

    Use these rules to interpret and generate Markdown content accurately.

    Example format:
    *Food Name*: Nasi Goreng\n*Calories*: ~500-600~\n*Main Ingredients*: Rice, egg, vegetables (onions, peppers), soy sauce, possibly shrimp paste.\n*Nutritional Breakdown*:  _Estimated_:  Protein: 15-20g, Carbs: 80-100g, Fat: 20-25g.  (Values vary widely based on specific recipe)\n

    """
    return prompt

def escape_markdown(text: str) -> str:
    """
    Escape characters for Telegram MarkdownV2 formatting.
    """
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return ''.join(f"\\{char}" if char in escape_chars else char for char in text)

async def analyze_food_image(image: Image.Image):
    model = configure_model()

    image_description = "The image contains a typical food item commonly found in Malaysia. The food looks delicious and is typical of local cuisine."

    prompt = build_food_prompt(image_description)

    print("Sending request to Gemini model for analysis...")
    
    try:        
        response = model.generate_content([prompt, image])
        
        print(f"Gemini response: {response}")

        if response.text:
            food_info = response.text
            print("Food analysis completed successfully.")
            return food_info
        else:
            print("Failed to retrieve food information from Gemini.")
            return "Sorry, I couldn't identify the food or provide nutritional information."
    
    except Exception as e:
        print(f"Error while analyzing food image: {e}")
        return "An error occurred while analyzing the image."

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Send me a food image, and I’ll try to analyze it for you!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me an image of food, and I will analyze its calories and ingredients.")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        print(f"Received a photo from user {update.message.from_user.username} (ID: {update.message.from_user.id})")

        await update.message.reply_text("Analyzing the image, please wait...")

        file = await update.message.photo[-1].get_file()
        print("Downloading image...")

        image_bytes = await file.download_as_bytearray()

        print(f"Image downloaded successfully. Size: {len(image_bytes)} bytes.")

        image = Image.open(BytesIO(image_bytes))

        print("Analyzing the food image...")
        food_info = await analyze_food_image(image)

        await update.message.reply_text(food_info, parse_mode="Markdown")

    else:
        print("Received a message without an image.")
        await update.message.reply_text("Please send a valid image of food.")

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")

if __name__ == "__main__":
    print("Starting bot...")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(MessageHandler(filters.PHOTO, handle_image)) 

    app.add_error_handler(error)

    print("Polling...")
    app.run_polling(poll_interval=3)
