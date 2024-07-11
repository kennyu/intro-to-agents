from quart import Quart, request
import openai
import time
import tiktoken
import os

app = Quart(__name__)

openai.api_key = os.environ.get("OPENAI_API_KEY")

def summarize(text, temperature=0.7, max_tokens=300, top_p=1, frequency_penalty=0, presence_penalty=0, model="gpt-4o"):
    ## split the text into chunks of 2000 tokens
    chunks = []
    chunk = ""
    chunk_length = 0
    encoding = tiktoken.encoding_for_model(model)
    tokenized_text = encoding.encode(text)
    for token in tokenized_text:
        if chunk_length > 3000:
            chunks.append(chunk)
            chunk = ""
            chunk_length = 0
        decoded_token = encoding.decode([token])
        if decoded_token == " " or decoded_token == "\n":
            continue
        chunk += decoded_token
        chunk_length += 1
    if chunk != "":
        chunks.append(chunk)
    print(f"summarizing {len(chunks)} chunks, 2 seconds per chunk is {len(chunks) * 2} seconds")
    ## give the context to the AI about how much text there is to summarize
    total_summary = ""
    for n, chunk in enumerate(chunks):
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {
                    "role":"system",
                    "content": f"Your role is to summarize - you may have a video, a long paper, or a webpage. This is {n} of {len(chunks)} parts of a larger whole. Respond only with the summary, and do not use the phrase 'the text' or refer to the text as 'the text', only summarize the points within the text, do not refer to the text, webpage, or video itself. This summary will be concatenated to other summaries of a larger document, in a recursive manner. The summary should be about 100 tokens long. Only summarize the main points. Your goal is to produce a summary for another AI to produce a lesson from, so please note any learning objectives covered in the text, and summarize this chunk of text in a way that would be useful for a student to learn from."
                },
                {
                "role": "user",
                "content": chunk
                }
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty
        )
        time.sleep(1)

        result = response.choices[0].message.content
        total_summary += "\nChunk " + str(n) + " of " + str(len(chunks)) + "\n" + result
    return total_summary


@app.route("/summarize", methods=["POST"])
async def summarize_endpoint():
    body = await request.get_data()
    body = body.decode("utf-8")
    return {
        "summary" : summarize(body)
    }

@app.route("/explain")
async def explain_endpoint():
    return "This is a summarization agent. It uses the OpenAI API to summarize text. Send a POST request to /summarize with the text you want to summarize as the body of the request."

@app.route("/")
async def index():
    return "Please send a post request to /summarize with the text you want to summarize as the body of the request."


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="8000")
