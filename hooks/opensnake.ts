import { connect } from "net";
import { homedir } from "os";

const SOCKET = `${process.env.XDG_RUNTIME_DIR || "/tmp"}/opensnake.sock`;

function send(action: string) {
  return new Promise<void>((resolve, reject) => {
    const client = connect(SOCKET, () => {
      client.write(JSON.stringify({ action }) + "\n");
    });
    client.on("data", () => {
      client.end();
      resolve();
    });
    client.on("error", reject);
    setTimeout(() => reject(new Error("timeout")), 2000);
  });
}

export async function onStatus(status: string) {
  if (status === "thinking") {
    await send("start").catch(() => {});
  } else if (status === "idle") {
    await send("stop").catch(() => {});
  }
}

export async function onIdle() {
  await send("stop").catch(() => {});
}
