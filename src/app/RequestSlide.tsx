import { Card, CardContent } from "@/components/ui/card"
import type { Order } from "@/app/page"

interface RequestSlideProps {
  request: Order
  index: number
}

export function RequestSlide({ request, index }: RequestSlideProps) {
  return (
    <Card className="h-full">
      <CardContent className="flex flex-col h-full p-6">
        <h3 className="text-lg font-semibold mb-4">Запрос #{index + 1}</h3>
        <div className="grid grid-cols-2 gap-4 flex-grow">
          <div>
            <h4 className="text-sm font-medium mb-2">Ячейки:</h4>
            <ul className="text-sm space-y-1">
              {request.cells.map((cell, idx) => (
                <li key={idx} className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
                  [{cell[0]}, {cell[1]}]
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-medium mb-2">Артикулы:</h4>
            <ul className="text-sm space-y-1">
              {Object.entries(request.selection.request).map(([key, value]) => (
                <li key={key} className="bg-green-100 text-green-800 px-2 py-1 rounded">
                  {key}: {value + " штук"}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

