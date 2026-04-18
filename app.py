import os
import gradio as gr
import google.generativeai as genai

# Integrate the provided Gemini API key
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
SYSTEM_PROMPT = "You are an AI Escape Room Game Master. Your task is to create and run an interactive text-based escape room game. You must maintain the player’s progress, inventory, and puzzle state. Your responses must always stay within the escape room domain. Be creative but ensure the puzzles are solvable in 3–5 steps."

INITIALIZATION_PROMPT = "Create a new escape room scenario. Provide a theme (e.g., Mysterious Library, Abandoned Lab, Haunted Mansion). Describe the room in 2–3 sentences. Then describe the first puzzle the player sees. End by asking the player what they want to do."

LOOK_PROMPT = "The player typed \"look\". Based on the current game state, describe the room again, including any objects, changes, or puzzles that are still unresolved. If there are new elements because of previous actions, mention them. Keep the description concise (max 3 sentences)."

INVENTORY_PROMPT = "The player typed \"inventory\". List the items the player currently has. If the inventory is empty, say so. Do not add new items unless the player has collected them earlier."

USE_PROMPT = "The player typed \"use {item}\". Decide if that item exists in the player’s inventory and if it can be used in the current situation. If it’s useful, describe what happens (e.g., opens a lock, reveals a clue). If it’s not useful or not present, give a hint about what might work. Update the game state accordingly."

HINT_PROMPT = "The player asked for a \"hint\". Provide a subtle clue about the current unsolved puzzle. Do not give the answer directly. The hint should be one short sentence."

SOLVE_PROMPT = "The player attempted to solve a puzzle with: \"{answer}\". Check if it matches the expected solution for the current puzzle. If correct: congratulate the player, describe what happens (door opens, new item appears, etc.), and present the next puzzle or declare the game finished. If incorrect: explain why it’s wrong and suggest they try again."

COMPLETION_PROMPT = "The player has solved all puzzles and escaped. Describe the escape in a celebratory way (2 sentences). Ask if they want to play again or reset."

RESET_PROMPT = "The player typed \"reset\". Reset the entire game to a new random scenario with a different theme. Start over from the initial room description and first puzzle."

UNKNOWN_PROMPT = "The player typed an action that is not one of the predefined commands (look, inventory, use, solve, hint, reset). Interpret it as a creative attempt (e.g., \"break the glass\"). Decide if it’s reasonable in the context. If it makes sense, describe the outcome and update the game state. If it’s impossible, explain why and suggest one of the valid commands. The action was: \"{action}\""

def get_model():
    return genai.GenerativeModel('gemini-2.5-flash', system_instruction=SYSTEM_PROMPT)

def start_game():
    model = get_model()
    try:
        response = model.generate_content(SYSTEM_PROMPT + "\n\nPlayer: " + INITIALIZATION_PROMPT + "\nGame Master:")
        reply = response.text
    except Exception as e:
        reply = f"Error starting game. Please check your API key: {e}"
    
    # Gradio history format: [ (user_msg, bot_msg), ... ]
    return [{"role": "assistant", "content": reply}]

def user_action(user_input, history):
    if not user_input or not user_input.strip():
        return "", history
        
    user_input_lower = user_input.strip().lower()
    model = get_model()
    
    if user_input_lower == "reset":
        try:
            response = model.generate_content(SYSTEM_PROMPT + "\n\nPlayer: " + RESET_PROMPT + "\nGame Master:")
            reply = response.text
        except Exception as e:
            reply = f"Error: {e}"
        return "", [{"role": "user", "content": user_input}, {"role": "assistant", "content": reply}]

    # Build transcript for Gemini
    transcript = SYSTEM_PROMPT + "\n\n"
    
    first_assistant = True
    for msg in history:
        role = msg.get("role") if isinstance(msg, dict) else msg.role
        content = msg.get("content") if isinstance(msg, dict) else msg.content
        
        if role == "assistant" and first_assistant:
            transcript += f"Player: {INITIALIZATION_PROMPT}\n"
            transcript += f"Game Master: {content}\n\n"
            first_assistant = False
        elif role == "user":
            transcript += f"Player: {content}\n"
        elif role == "assistant":
            transcript += f"Game Master: {content}\n\n"
            
    if user_input_lower == "look":
        current_prompt = LOOK_PROMPT
    elif user_input_lower == "inventory":
        current_prompt = INVENTORY_PROMPT
    elif user_input_lower.startswith("use "):
        item = user_input.replace("use ", "", 1).strip()
        current_prompt = USE_PROMPT.format(item=item)
    elif user_input_lower == "hint":
        current_prompt = HINT_PROMPT
    elif user_input_lower.startswith("solve "):
        answer = user_input.replace("solve ", "", 1).strip()
        current_prompt = SOLVE_PROMPT.format(answer=answer)
    else:
        current_prompt = UNKNOWN_PROMPT.format(action=user_input)
        
    transcript += f"Player: {current_prompt}\nGame Master: "
    
    try:
        response = model.generate_content(transcript)
        reply = response.text
    except Exception as e:
        reply = f"Error: {e}"
        
    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": reply})
    return "", history

css = """
/* Base Theme: Dark & Mysterious Egyptian Adventure */
body, .gradio-container {
    background-color: #0a0c10 !important;
    color: #e0e0e0 !important;
    font-family: 'Courier New', Courier, monospace !important;
}

/* Typography & Glowing Accents */
h1, h2, h3, h4, h5, h6, strong {
    color: #f5c542 !important;
    text-shadow: 0 0 10px rgba(245, 197, 66, 0.4);
}

/* Chatbot Styling */
#chatbot-container {
    height: 65vh !important;
    border: 1px solid #f5c542 !important;
    border-radius: 8px;
    background: #11141c !important;
    box-shadow: 0 0 15px rgba(245, 197, 66, 0.1);
    padding: 10px;
}

/* Chat Bubbles & Animations */
.message-wrap .message {
    animation: pulseBubble 0.3s ease-out;
}
.message.bot {
    background-color: #1a1e29 !important;
    border: 1px solid #f5c542 !important;
    color: #f5c542 !important;
    box-shadow: 0 0 10px rgba(245, 197, 66, 0.1);
}
.message.user {
    background-color: #2a3142 !important;
    color: #ffffff !important;
    border: 1px solid #444 !important;
}

@keyframes pulseBubble {
    0% { transform: scale(0.98); opacity: 0; }
    100% { transform: scale(1); opacity: 1; }
}

/* Input Area Glow */
#action-input input {
    background: #0a0c10 !important;
    border: 1px solid #444 !important;
    color: #f5c542 !important;
    transition: all 0.3s ease;
}
#action-input input:focus {
    border-color: #f5c542 !important;
    box-shadow: 0 0 15px rgba(245, 197, 66, 0.5) !important;
    outline: none !important;
}

/* Buttons */
.submit-btn {
    background-color: #f5c542 !important;
    color: #0a0c10 !important;
    font-weight: bold !important;
    border: none !important;
    transition: all 0.2s ease;
}
.submit-btn:hover {
    box-shadow: 0 0 15px rgba(245, 197, 66, 0.8) !important;
    transform: scale(1.02);
}

.reset-btn {
    background-color: transparent !important;
    color: #ff4c4c !important;
    border: 1px solid #ff4c4c !important;
    transition: all 0.2s ease;
}
.reset-btn:hover {
    background-color: #ff4c4c !important;
    color: #0a0c10 !important;
    box-shadow: 0 0 15px rgba(255, 76, 76, 0.6) !important;
}

/* Custom Footer */
.custom-footer {
    text-align: center;
    margin-top: 25px;
    font-size: 0.8rem;
    color: #555;
    font-family: Arial, sans-serif !important;
    letter-spacing: 1px;
}
"""

with gr.Blocks(title="AI Escape Room", css=css, theme=gr.themes.Monochrome()) as demo:
    with gr.Row():
        # Sidebar Layer
        with gr.Column(scale=1, min_width=250):
            gr.Markdown("# 👁️ The AI Escape")
            gr.Markdown("### 📜 Ancient Commands\n\n- `look`\n- `inventory`\n- `use [item]`\n- `hint`\n- `solve [answer]`\n\n*Or try any creative action!*")
            reset_btn = gr.Button("🔥 Reset Destiny", elem_classes="reset-btn")
        
        # Main Game Layer
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(elem_id="chatbot-container", show_label=False)
            with gr.Row():
                msg = gr.Textbox(placeholder="What do you want to do?", show_label=False, elem_id="action-input", scale=4, autofocus=True)
                submit_btn = gr.Button("Submit", elem_classes="submit-btn", scale=1)
                
    # Footer
    gr.HTML("<div class='custom-footer'>© 2026 Aniket Singh – AI Escape Room Generator</div>")
    
    # Initialize game on load
    demo.load(start_game, inputs=None, outputs=[chatbot])
    
    # Submit action handling
    msg.submit(user_action, [msg, chatbot], [msg, chatbot])
    submit_btn.click(user_action, [msg, chatbot], [msg, chatbot])
    
    # Reset button handling triggers "reset" automatically
    reset_btn.click(lambda h: user_action("reset", h), inputs=[chatbot], outputs=[msg, chatbot])

if __name__ == "__main__":
    demo.launch(inbrowser=True)
