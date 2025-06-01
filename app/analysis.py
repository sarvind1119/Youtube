from nltk.sentiment.vader import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def classify_sentiment(text):
    score = analyzer.polarity_scores(text)["compound"]
    if score >= 0.3:
        return "Positive"
    elif score <= -0.3:
        return "Negative"
    else:
        return "Neutral"

def analyze_comments(comments):
    sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
    labeled_comments = []

    for comment in comments:
        sentiment = classify_sentiment(comment["text"])
        sentiment_counts[sentiment] += 1
        comment["sentiment"] = sentiment
        labeled_comments.append(comment)

    total = len(labeled_comments)
    percentages = {k: round((v / total) * 100, 2) for k, v in sentiment_counts.items()}

    return {
        "sentiment_distribution": percentages,
        "labeled_comments": labeled_comments,
    }
