from config import OPENAI_API_KEY

def main():
    if OPENAI_API_KEY:
        print("SARMA is connected to an AI provider")
    else:
        print("SARMA is running without an API key")

if __name__ == "__main__":
    main()