package main

import (
	"encoding/json"
	"fmt"
	"mypropertyqr-landsurvey/Algs"
)



func main() {
	Algs.InitPy()


	response := Algs.Pycess(Algs.PyParam{
		Mod: "ExtractPdf",
		Arg: []any{"1.pdf"},
	})


	var res Algs.PyRes
	err := json.Unmarshal([]byte(response), &res)
	if err != nil {
		fmt.Println("JSON error:", err)
		return
	}

	res.Line3 = Algs.RemoveFloatingLines(res.Line3)
	res.Line1 = Algs.RemoveFloatingLines(res.Line1)

    Algs.OffsetToOrigin(&res)

	seen := make(map[string]bool)
	var points []Algs.Point

	for _, seg := range res.Line3 {
		for _, p := range seg {
			key := fmt.Sprintf("%.2f_%.2f", p[0], p[1])
			if !seen[key] {
				seen[key] = true
				points = append(points, Algs.Point{p[0], p[1]})
			}
		}
	}
	for _, seg := range res.Line1 {
		for _, p := range seg {
			key := fmt.Sprintf("%.2f_%.2f", p[0], p[1])
			if !seen[key] {
				seen[key] = true
				points = append(points, Algs.Point{p[0], p[1]})
			}
		}
	}
    //all red text with coordinates ((x,y):text)    
	CoordRed := Algs.RankBasedAssignment(points, res.R)
    CoordBlue := Algs.FormatBbox(res.B)

    CoordRedMap := make(map[Algs.Point]string)
    for key, value := range CoordRed {
        CoordRedMap[value] = key
    }

    // get subdiv
    str, err := json.Marshal([]any{CoordBlue, res.Line1, res.Line3, res.Xmax - res.Xmin, res.Ymax - res.Ymin})
    if err != nil {
        fmt.Println("Error marshaling Line1 to JSON:", err)
    }
    response = Algs.Pycess(Algs.PyParam{
		Mod: "getSubdiv",
		Arg: []any{string(str)},
	})

    var subdivResult map[string][][][]float32
    err = json.Unmarshal([]byte(response), &subdivResult)
    if err != nil {
        fmt.Println("Error unmarshaling subdiv JSON:", err)
        return
    }


    for ind := range CoordBlue {
        subdivResult[ind] = Algs.OrderLines(subdivResult[ind])
    }


//remove line if dont have text
    for ind := range subdivResult {
        newPol := [][][]float32{}
        for _, pol := range subdivResult[ind] {
            newLne := [][]float32{}
            for _, lne := range pol {
                _, exists := CoordRedMap[Algs.Point{lne[0], lne[1]}]
                if exists {
                    newLne = append(newLne, lne)
                }
            }
            newPol = append(newPol, newLne)
        }
        subdivResult[ind] = newPol
    }

    // fmt.Println(subdivResult)   
    // fmt.Println(Algs.FlattenPoints(subdivResult["3"]))

	coordinates := make(map[string][]any)
	for c := range CoordRed {
		temp := CoordRed[c]
		coordinates[c] = []any{[]float32{temp.X, temp.Y}, "main", []string{"notmodified", "notmodified"}}
	}

	lines := make([]map[string]any, 0, len(res.Line3))
	for _, seg := range res.Line3 {
		lines = append(lines, map[string]any{
			"coordinates": []string{CoordRedMap[Algs.Point{seg[0][0], seg[0][1]}], CoordRedMap[Algs.Point{seg[1][0], seg[1][1]}]},
			"length":      Algs.Distance(Algs.Point{seg[0][0], seg[0][1]}, Algs.Point{seg[1][0], seg[1][1]}),
			"dashes":      "[ 9 0 ] 1",
			"strokewidth": "2",
		})
	}

	for _, subdivPolys := range subdivResult {
		for _, poly := range subdivPolys {
			// Each poly is a slice of lines (each line is []float32{X, Y})
			for i := 0; i < len(poly)-1; i++ {
				start := poly[i]
				end := poly[i+1]
				lines = append(lines, map[string]any{
					"coordinates": []string{
						CoordRedMap[Algs.Point{start[0], start[1]}],
						CoordRedMap[Algs.Point{end[0], end[1]}],
					},
					"length":      Algs.Distance(Algs.Point{start[0], start[1]}, Algs.Point{end[0], end[1]}),
					"dashes":      "[ 30 10 1 3 1 3 1 10 ] 1",
					"strokewidth": "1",
				})
			}
		}
	}


	data, err := json.Marshal(map[string]any{"lines": lines, "coordinates": coordinates})
	if err != nil {
		fmt.Println("Error marshaling lines:", err)
	} else {
		fmt.Println(string(data))
	}

	
}