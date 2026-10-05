benchmark['result'] = {
	"messages": [
		{"type": "text",     "from": "Alice", "id": "m1", "timestamp": "t1", "body": "hello"},
		{"type": "reaction", "from": "Bob",   "id": "m2", "timestamp": "t2", "emoji": "👍", "message_id": "m1"},
		{"type": "image",    "from": "Alice", "id": "m3", "timestamp": "t3", "url": "http://example.com/img.jpg"}
	]
}
