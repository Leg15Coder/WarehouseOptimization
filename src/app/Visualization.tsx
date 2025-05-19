"use client"

import {VisuallyHidden} from "@radix-ui/react-visually-hidden";
import {Dialog, DialogContent, DialogTitle, DialogTrigger, DialogClose} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { useState } from "react"

interface FullScreenVisualizationProps {
  warehouse: boolean[][]
  coordinates: [number, number][]
}

export function Visualization({ warehouse, coordinates }: FullScreenVisualizationProps) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <VisuallyHidden asChild>
        <DialogTitle>Visualization</DialogTitle>
      </VisuallyHidden>
      <DialogTrigger asChild>
        <Button>Открыть полноэкранную визуализацию</Button>
      </DialogTrigger>
      <DialogContent className="max-w-[95vw] w-full h-[95vh] p-6 overflow-auto" aria-describedby={undefined}>
        <DialogClose className='fixed m-2'>a
        </DialogClose>
        <div className="w-full h-full flex items-center justify-center">
          <div
            className="grid"
            style={{
              gridTemplateColumns: `repeat(${warehouse[0].length}, minmax(0.5rem, 1fr))`,
              maxWidth: "100%",
              maxHeight: "100%",
              rowGap: "1px",
              columnGap: "0.1px"
            }}
          >
            {warehouse.flatMap((row, i) =>
              row.map((cell, j) => (
                <div
                  key={`${i}-${j}`}
                  style={{width: "2px", height: "3px"}}
                  className={`aspect-auto ${
                    coordinates.some(([x, y]) => x === j && y === i)
                      ? "bg-red-500"
                      : cell
                        ? "bg-blue-500"
                        : "bg-gray-200"
                  }`}
                />
              )),
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

