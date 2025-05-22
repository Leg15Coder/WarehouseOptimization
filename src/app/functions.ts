import * as XLSX from "xlsx";

export const excelToJson = async (file: File): Promise<Array<Record<string, number>>> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const workbook = XLSX.read(data, { type: "array" });

        const sheetName = workbook.SheetNames[0];
        const sheet = workbook.Sheets[sheetName];

        const jsonData: Array<Record<string, number>> = XLSX.utils.sheet_to_json(sheet);
        resolve(jsonData);
      } catch (error) {
        reject(error);
      }
    };

    reader.onerror = (error) => {
      reject(error);
    };

    reader.readAsArrayBuffer(file);
  });
};

export const getMargin = (side: string, cell: number[], warehouse: boolean[][]) : boolean => {
  // console.log(warehouse[78][0])
  const x: number = cell[0];
  const y: number = cell[1];
  switch (side) {
    case "left": 
      if (y <= 0) {
        return true;
      }
      return warehouse[x][y] != warehouse[x][y - 1];
    case "right":
      if (y >= warehouse[0].length - 1) {
        return true;
      }
      return warehouse[x][y] != warehouse[x][y + 1];
    case "bottom":
      if (x >= warehouse.length - 1) {
        return true;
      }
      return warehouse[x][y] != warehouse[x + 1][y];
    case "top":
      if (x <= 0) {
        return true;
      }
      return warehouse[x][y] != warehouse[x - 1][y];
  }
  return true
}
