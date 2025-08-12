import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useState } from "react";

const Chatbot = () => {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<
    Array<{ type: "user" | "bot"; content: string }>
  >([
    {
      type: "bot",
      content:
        "Hello! I'm your assistant for flight anomaly detection. How can I help you today?",
    },
  ]);

  const handleSendMessage = () => {
    if (message.trim()) {
      setChatHistory((prev) => [...prev, { type: "user", content: message }]);
      setTimeout(() => {
        setChatHistory((prev) => [
          ...prev,
          {
            type: "bot",
            content:
              "I understand you're asking about: \"" +
              message +
              '". This will be connected to the RAG system soon!',
          },
        ]);
      }, 800);
      setMessage("");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSendMessage();
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-xl font-semibold tracking-widest uppercase">
          AI Chatbot
        </h1>
        <p className="text-sm text-muted-foreground">
          Ask questions about flight anomalies and get intelligent responses
        </p>
      </div>

      <Card className="flex h-[600px] flex-col">
        <CardHeader>
          <CardTitle>Flight Anomaly Assistant</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-1 flex-col">
          <div className="mb-4 flex-1 space-y-4 overflow-y-auto rounded-lg bg-muted/20 p-4">
            {chatHistory.map((chat, index) => (
              <div
                key={index}
                className={`flex ${
                  chat.type === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-xs rounded-lg px-4 py-2 text-sm md:max-w-md ${
                    chat.type === "user"
                      ? "bg-primary text-primary-foreground"
                      : "border bg-card text-foreground"
                  }`}
                >
                  {chat.content}
                </div>
              </div>
            ))}
          </div>

          <div className="flex gap-2">
            <div className="flex-1">
              <Label htmlFor="message-input" className="sr-only">
                Type your message
              </Label>
              <Input
                id="message-input"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about anomalies, routes, or detection results…"
              />
            </div>
            <Button onClick={handleSendMessage} disabled={!message.trim()}>
              Send
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Chatbot;
