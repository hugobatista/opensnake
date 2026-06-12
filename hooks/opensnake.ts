import type { Plugin } from "@opencode-ai/plugin"
import { connect } from "net"

const SOCKET = `${process.env.XDG_RUNTIME_DIR || "/tmp"}/opensnake.sock`

function send(action: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const client = connect(SOCKET, () => {
      client.write(`${JSON.stringify({ action })}\n`)
    })
    client.on("data", () => {
      client.end()
      resolve()
    })
    client.on("error", reject)
    setTimeout(() => reject(new Error("timeout")), 2000)
  })
}

export const OpenSnake: Plugin = async () => {
  let running = false

  return {
    event: async ({ event }) => {
      if (
        event.type === "session.status"
        && event.properties?.status?.type === "busy"
        && !running
      ) {
        running = true
        await send("start").catch(() => {
          running = false
        })
      } else if (event.type === "session.idle" && running) {
        running = false
        await send("stop").catch(() => {})
      }
    },
  }
}
