export class WsClient {
    constructor(url, { onMessage, reconnectDelayMs = 2000 } = {}) {
        this.url = url;
        this.onMessage = onMessage;
        this.reconnectDelayMs = reconnectDelayMs;
        this.connected = false;
        this.socket = null;
        this._connect();
    }

    _connect() {
        this.socket = new WebSocket(this.url);
        this.socket.addEventListener("open", () => {
            this.connected = true;
        });
        this.socket.addEventListener("message", (event) => {
            this.onMessage(event.data, Date.now());
        });
        this.socket.addEventListener("close", () => {
            this.connected = false;
            setTimeout(() => this._connect(), this.reconnectDelayMs);
        });
        this.socket.addEventListener("error", () => {
            this.socket.close();
        });
    }
}
