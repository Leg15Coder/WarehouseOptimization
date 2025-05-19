"use client"

import type React from "react"
import { useEffect, useLayoutEffect, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import FileUpload from "@/app/FileLoader"
import { useToast } from "@/hooks/use-toast"
import { Toaster } from "@/components/ui/toaster"

type PathPoint = any[]

type Good = { sku: number; name: string; product_type: string }

export type Order = {
  type: "request"
  message: string
  data: {
    worker_id: number
    moving_cells: PathPoint[]
    selected_products: Record<string, number>
  }
}

export default function Home() {
  const [warehouse, setWarehouse] = useState<boolean[][]>([])
  const [path, setPath] = useState<PathPoint[]>([])
  const [requests, setRequests] = useState<Order[]>([])
  const [animationActive, setAnimationActive] = useState(false)
  const [step, setStep] = useState(0)

  const { toast } = useToast()

  const socket = useRef<WebSocket | null>(null)
  const gridRef = useRef<HTMLDivElement>(null)

  // WebSocket initialization
  useLayoutEffect(() => {
    const ws = new WebSocket("ws://192.168.131.106:8765")
    ws.onopen = () => {
      console.log("Connected to the server")
      socket.current = ws
    }
    ws.onmessage = (e) => {
      const parsed: Order = JSON.parse(e.data)
      if (parsed.type == "request") {
        console.log(parsed)
        setRequests((prev) => [...prev, parsed])
        toast({
          title: "Пришел новый заказ",
          description: `Заказ для курьера ${parsed.data.worker_id}`,
          duration: 5000,
        })
      } else {
        console.log("Received not a request:")
        console.log(parsed)
      }
    }
    if (requests.length > 2) {
      ws.close()
    }
    return () => ws.close()
  }, [])

  // useLayoutEffect(() => {
  //   if (!socket.current) return
  //   socket.current.send(
  //     JSON.stringify({
  //       auth: "secret_token",
  //       type: "create_warehouse",
  //       payload: { layout: warehouse },
  //     }),
  //   )
  // }, [warehouse])

  // Expose helper functions
  useLayoutEffect(() => {
    window.sendGoods = (raw: any[][]) => {
      const goods: Good[] = raw.map(([sku, name, product_type]) => ({ sku, name, product_type }))
      socket.current?.send(JSON.stringify({ auth: "secret_token", type: "create_product_type", payload: goods }))
    }
    window.getActualGoods = () =>
      socket.current?.send(JSON.stringify({ auth: "secret_token", type: "list_product_types" }))
    window.getServerStatus = () => socket.current?.send(JSON.stringify({ auth: "secret_token", type: "run" }))
  }, [])

  const visualizeOrder = (index: number) => {
    const order = requests[index]
    const raw_moving = order.data.moving_cells[0]
    const moving = []
    for (let i = 0; i < raw_moving.length; ++i) {
      const current_cell: PathPoint = raw_moving[i]
      if (current_cell[2] == "product") {
        if (i > 0) {
          moving.push(raw_moving[i - 1])
        }
        moving.push(raw_moving[i])
      } else {
        if (i > 0 && raw_moving[i - 1][2] != "product") {
          const prev_cell = raw_moving[i - 1]
          const offset: number[] = [Math.sign(current_cell[0] - prev_cell[0]), Math.sign(current_cell[1] - prev_cell[1])]
          let moving_cell = prev_cell
          while (moving_cell[0] != current_cell[0] || moving_cell[1] != current_cell[1]) {
            moving.push(moving_cell)
            moving_cell = [moving_cell[0] + offset[0], moving_cell[1] + offset[1]]
          }
        }
      }
    }
    moving.push(raw_moving[raw_moving.length - 1])
    setPath(moving)
    setStep(0)
    setAnimationActive(true)
    if (gridRef.current && moving.length) {
      const [sx, sy] = [moving[0][0], moving[0][1]]
      const cell = gridRef.current.querySelector(`div[data-row='${sx}'][data-col='${sy}']`) as HTMLElement
      cell.scrollIntoView({ behavior: "smooth" })
    }
  }

  const intervalMs = 100
  useEffect(() => {
    if (!animationActive || path.length === 0) return
    const id = setInterval(() => {
      setStep((prev) => Math.min(prev + 1, path.length - 1))
    }, intervalMs)
    return () => clearInterval(id)
  }, [animationActive, path])

  const cellSize = 8
  const gap = 1
  const headSize = cellSize * 0.6
  const offset = cellSize * 0.2
  const rows = warehouse.length
  const cols = warehouse[0]?.length || 0
  const headPoint = path[step]
  const headStyle: React.CSSProperties = headPoint
    ? {
      position: "absolute",
      width: headSize,
      height: headSize,
      borderRadius: "50%",
      backgroundColor: "tomato",
      pointerEvents: "none",
      top: headPoint[0] * (cellSize + gap) + offset,
      left: headPoint[1] * (cellSize + gap) + offset,
    }
    : { display: "none" }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 sm:p-8">
      <Card className="w-full max-w-4xl">
        <CardContent className="p-6">
          <FileUpload setWarehouseAction={setWarehouse} />
          <Card className="mt-4">
            <CardContent className="p-4">
              {rows > 0 ? (
                <div
                  ref={gridRef}
                  style={{
                    position: "relative",
                    scrollBehavior: "smooth",
                    display: "grid",
                    overflow: "auto",
                    gridTemplateColumns: `repeat(${cols}, ${cellSize}px)`,
                    gridTemplateRows: `repeat(${rows}, ${cellSize}px)`,
                    gap: `${gap}px`,
                  }}
                >
                  {warehouse.flatMap((row, i) =>
                    row.map((cell, j) => {
                      // Красим product-наборы и проходы по lastPath
                      const idxPath = path.findIndex((p) => p[0] === i && p[1] === j && p[2] === "product")
                      const visited = idxPath !== -1 && idxPath <= step
                      const isProd = idxPath !== -1
                      const bgClass = isProd
                        ? visited
                          ? "bg-yellow-500"
                          : "bg-red-500"
                        : cell
                          ? "bg-blue-500"
                          : "bg-gray-200"
                      return <div key={`${i}-${j}`} data-row={i} data-col={j} className={bgClass} />
                    }),
                  )}
                  <div style={headStyle} />
                </div>
              ) : (
                <p>Загрузите файл для отображения схемы</p>
              )}
            </CardContent>
          </Card>

          {/* Кнопки генерации и общий visual */}
          {rows > 0 && (
            <CardContent className="p-0 flex flex-col items-center justify-center">
              <CardContent className="flex flex-row pb-0"></CardContent>

              {/* Список заказов */}
              {requests.length > 0 && (
                <div className="w-full max-w-4xl mt-6 space-y-4">
                  <h2 className="text-xl font-semibold">Список заказов</h2>
                  {requests.map((order, idx) => (
                    <Card key={idx} className="">
                      <CardContent className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="font-medium mt-3">
                            Заказ №{idx + 1} --- Курьер {order.data.worker_id}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <ul className="list-disc list-inside pl-4">
                            {Object.entries(order.data.selected_products).map(([sku, qty]) => (
                              <li key={sku}>
                                SKU {sku}: {qty} шт.
                              </li>
                            ))}
                          </ul>
                          <Button className="my-auto" onClick={() => visualizeOrder(idx)}>
                            Визуализировать
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          )}
        </CardContent>
      </Card>
      <Toaster />
    </main>
  )
}
