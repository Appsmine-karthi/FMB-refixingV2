package Algs

import (
	"encoding/json"
	"fmt"
	"math"
	"sort"
	"bytes"
	"io"
	"net/http"
	"os"
)

var PythonServer string

func LoadEnv(){
	PythonServer = os.Getenv("PYTHON_SERVER")
}

func doPost(url string, body []byte) (map[string]interface{}, error) {

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		response := map[string]interface{}{"error": resp.StatusCode, "link": url, "payload": body}
		return response, fmt.Errorf("received non-200 response: %d", resp.StatusCode)
	}

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var result map[string]interface{}
	err = json.Unmarshal(respBody, &result)
	if err != nil {
		fmt.Println(err)
		response := map[string]interface{}{"error": "error in unmarshalling","link":url,"payload":body}
		return response, fmt.Errorf("received non-200 response: %d", resp.StatusCode)
	}

	return result, nil

}


type PyParam struct {
	Mod string `json:"mod"`
	Arg []any  `json:"arg"`
}


func Pycess(det PyParam) (string,error) {

	jsonBytes, err := json.Marshal(det)
	if err != nil {
		panic(err)
	}

	response, err := doPost(PythonServer, jsonBytes)
	if err != nil {
		fmt.Println("doPost/process:", err)
		panic(err)
	}

	rtn := response["received"].(string)	
	if rtn[0] == '!'{
		return "",fmt.Errorf(rtn)
	}
	return rtn,nil

}

type Point struct {
	X, Y float32
}
type Label struct {
	Text string
	Bbox []float32
}
type PyRes struct {
	Line1   [][][]float32 `json:"line1"`
	Line1_  [][][]float32 `json:"line1_"`
	Line3   [][][]float32 `json:"line3"`
	R       []Label       `json:"r"`    
	B       []Label       `json:"b"`
	Xmin    float32       `json:"xmin"`
	Ymin    float32       `json:"ymin"`
	Xmax    float32       `json:"xmax"`
	Ymax    float32       `json:"ymax"`
	Scale    float32       `json:"scale"`
}

func RemoveFloatingLines(lines [][][]float32) [][][]float32 {
	type Point struct {
		X float32
		Y float32
	}

	pointCount := make(map[Point]int)
	for _, line := range lines {
		a := Point{line[0][0], line[0][1]}
		b := Point{line[1][0], line[1][1]}
		pointCount[a]++
		pointCount[b]++
	}

	var result [][][]float32
	for _, line := range lines {
		a := Point{line[0][0], line[0][1]}
		b := Point{line[1][0], line[1][1]}

		if pointCount[a] > 1 && pointCount[b] > 1 {
			result = append(result, line)
		}
	}

	return result
}

func RemoveIsolatedLines(lines [][][]float32) [][][]float32 {
	type Point struct {
		X float32
		Y float32
	}

	type Line struct {
		A Point
		B Point
	}

	pointToLines := make(map[Point][]int)
	pointCount := make(map[Point]int)

	// Preprocess to map points to lines
	for i, line := range lines {
		a := Point{line[0][0], line[0][1]}
		b := Point{line[1][0], line[1][1]}
		pointToLines[a] = append(pointToLines[a], i)
		pointToLines[b] = append(pointToLines[b], i)
		pointCount[a]++
		pointCount[b]++
	}

	visited := make([]bool, len(lines))
	var result [][][]float32

	// Find connected components (islands)
	for i := 0; i < len(lines); i++ {
		if visited[i] {
			continue
		}

		queue := []int{i}
		island := []int{}

		for len(queue) > 0 {
			curr := queue[0]
			queue = queue[1:]

			if visited[curr] {
				continue
			}
			visited[curr] = true
			island = append(island, curr)

			currLine := lines[curr]
			a := Point{currLine[0][0], currLine[0][1]}
			b := Point{currLine[1][0], currLine[1][1]}

			for _, nei := range pointToLines[a] {
				if !visited[nei] {
					queue = append(queue, nei)
				}
			}
			for _, nei := range pointToLines[b] {
				if !visited[nei] {
					queue = append(queue, nei)
				}
			}
		}

		// Only include the island if it has 4 or more lines
		if len(island) >= 4 {
			for _, idx := range island {
				result = append(result, lines[idx])
			}
		}
	}

	return result
}


type MatchCandidate struct {
	Point  Point
	Label  string
	Center Point
	Dist   float32
}

func Center(bbox []float32) Point {
	return Point{
		X: (bbox[0] + bbox[2]) / 2,
		Y: (bbox[1] + bbox[3]) / 2,
	}
}

func Distance(a, b Point) float32 {
	dx := a.X - b.X
	dy := a.Y - b.Y
	return float32(math.Sqrt(float64(dx*dx + dy*dy)))
}


func RankBasedAssignment(points []Point, labels []Label) map[string]Point {
	// Step 1: Create all (point, label, distance) tuples
	var candidates []MatchCandidate

	for _, pt := range points {
		for _, lbl := range labels {
			center := Center(lbl.Bbox)
			candidates = append(candidates, MatchCandidate{
				Point:  pt,
				Label:  lbl.Text,
				Center: center,
				Dist:   Distance(pt, center),
			})
		}
	}

	// Step 2: Sort by distance (ascending)
	sort.Slice(candidates, func(i, j int) bool {
		return candidates[i].Dist < candidates[j].Dist
	})

	// Step 3: Assign unique labels to points
	assignedPoints := make(map[string]bool)
	usedLabels := make(map[string]bool)
	finalMatches := make(map[string]Point)

	for _, c := range candidates {
		pkey := fmt.Sprintf("%.2f_%.2f", c.Point.X, c.Point.Y)

		if !assignedPoints[pkey] && !usedLabels[c.Label] {
			finalMatches[c.Label] = c.Point
			assignedPoints[pkey] = true
			usedLabels[c.Label] = true
		}
	}

	return finalMatches
}

func FormatBbox(labels []Label) map[string]Point {
	rtn := make(map[string]Point)
	for _, label := range labels {
		cx := float32(math.Round(float64((label.Bbox[0] + label.Bbox[2]) / 2)))
		cy := float32(math.Round(float64((label.Bbox[1] + label.Bbox[3]) / 2)))
		rtn[label.Text] = Point{cx, cy}
	}
	return rtn
}

func OffsetToOrigin(res *PyRes) {

	minX := float32(10000)
	minY := float32(10000)
	maxX := float32(0)
	maxY := float32(0)
	
	processLines := func(lines [][][]float32) {
		for _, line := range lines {
			for _, point := range line {
				if len(point) == 2 {
					x := point[0]
					y := point[1]
					if x < minX {
						minX = x
					}
					if y < minY {
						minY = y
					}
					if x > maxX {
						maxX = x
					}
					if y > maxY {
						maxY = y
					}
				}
			}
		}
	}

	processLines(res.Line1)
	processLines(res.Line1_)
	processLines(res.Line3)

	for _, label := range append(res.R, res.B...) {
		if len(label.Bbox) == 4 {
			x := label.Bbox[0]
			y := label.Bbox[1]
			if x < minX {
				minX = x
			}
			if y < minY {
				minY = y
			}
			if x > maxX {
				maxX = x
			}
			if y > maxY {
				maxY = y
			}

			x = label.Bbox[2]
			y = label.Bbox[3]
			if x < minX {
				minX = x
			}
			if y < minY {
				minY = y
			}
			if x > maxX {
				maxX = x
			}
			if y > maxY {
				maxY = y
			}
		}
	}

	// Step 2: Offset everything by minX, minY
	offsetLines := func(lines [][][]float32) {
		for i := range lines {
			for j := range lines[i] {
				lines[i][j][0] -= minX
				lines[i][j][1] -= minY
			}
		}
	}

	minX = float32(math.Floor(float64(minX)))
	minY = float32(math.Floor(float64(minY)))

	res.Xmin = minX
	res.Ymin = minY
	res.Xmax = maxX
	res.Ymax = maxY

	offsetLines(res.Line1)
	offsetLines(res.Line1_)
	offsetLines(res.Line3)

	for i := range res.R {
		res.R[i].Bbox[0] -= minX
		res.R[i].Bbox[1] -= minY
		res.R[i].Bbox[2] -= minX
		res.R[i].Bbox[3] -= minY
	}
	for i := range res.B {
		res.B[i].Bbox[0] -= minX
		res.B[i].Bbox[1] -= minY
		res.B[i].Bbox[2] -= minX
		res.B[i].Bbox[3] -= minY
	}

}

func equal(a, b []float32) bool {
	return len(a) == 2 && len(b) == 2 && a[0] == b[0] && a[1] == b[1]
}

func OrderLines(segments [][][]float32) [][][]float32 {
	var bestChain [][][]float32

	// Try each segment as a starting point
	for i := range segments {
		used := make([]bool, len(segments))
		chain := [][][]float32{segments[i]}
		used[i] = true
		last := segments[i][1]

		extended := true
		for extended {
			extended = false
			for j := range segments {
				if used[j] {
					continue
				}
				start := segments[j][0]
				end := segments[j][1]

				if start[0] == last[0] && start[1] == last[1] {
					chain = append(chain, segments[j])
					last = end
					used[j] = true
					extended = true
					break
				} else if end[0] == last[0] && end[1] == last[1] {
					// reverse the segment
					chain = append(chain, [][]float32{end, start})
					last = start
					used[j] = true
					extended = true
					break
				}
			}
		}

		if len(chain) > len(bestChain) {
			bestChain = chain
		}
	}



	return bestChain
}

func FlattenPoints(segments [][][]float32) [][]float32 {
	var points [][]float32
	for _, segment := range segments {
		if len(segment) != 2 {
			continue // skip incomplete/unconnected segments
		}
		if len(points) == 0 || !equal(points[len(points)-1], segment[0]) {
			points = append(points, segment[0])
		}
		points = append(points, segment[1])
	}
	return points
}

func CalculateArea(points [][]float32) float32 {
	var area float32
	for i := 0; i < len(points)-1; i++ {
		x1, y1 := points[i][0], points[i][1]
		x2, y2 := points[i+1][0], points[i+1][1]
		area += (x1 * y2) - (x2 * y1)
	}
	return float32(math.Abs(float64(area)) / 2.0)
}

func GetBoundingBox(lines [][][]float32) (xmin, ymin, xmax, ymax float32) {
	if len(lines) == 0 {
		return 0, 0, 0, 0
	}
	xmin, ymin = lines[0][0][0], lines[0][0][1]
	xmax, ymax = lines[0][0][0], lines[0][0][1]
	for _, seg := range lines {
		for _, pt := range seg {
			x, y := pt[0], pt[1]
			if x < xmin {
				xmin = x
			}
			if x > xmax {
				xmax = x
			}
			if y < ymin {
				ymin = y
			}
			if y > ymax {
				ymax = y
			}
		}
	}
	return xmin, ymin, xmax, ymax
}

func pointsEqual(p1, p2 []float32) bool {
	const eps = 0.001
	return math.Abs(float64(p1[0]-p2[0])) < eps && math.Abs(float64(p1[1]-p2[1])) < eps
}

func pointKey(p []float32) string {
	return fmt.Sprintf("%.1f,%.1f", p[0], p[1])
}

func is_valid_triangle(p1, p2, p3 []float32) bool {
	xmin, ymin := p1[0], p1[1]
	xmax, ymax := p1[0], p1[1]

	points := [][]float32{p2, p3}
	for _, pt := range points {
		if pt[0] < xmin {
			xmin = pt[0]
		}
		if pt[0] > xmax {
			xmax = pt[0]
		}
		if pt[1] < ymin {
			ymin = pt[1]
		}
		if pt[1] > ymax {
			ymax = pt[1]
		}
	}

	length := xmax - xmin
	width := ymax - ymin

	// fmt.Println("arrow, L=",length)
	// fmt.Println("arrow, W=",width)
	// fmt.Println("\n")

	return length <= 50 && width <= 50
}

func RemoveArrows(lines [][][]float32) [][][]float32 {
	type Point [2]float32
	pointToLines := make(map[Point][]int)

	toPoint := func(p []float32) Point {
		return Point{p[0], p[1]}
	}

	for i, line := range lines {
		start := toPoint(line[0])
		end := toPoint(line[1])
		pointToLines[start] = append(pointToLines[start], i)
		pointToLines[end] = append(pointToLines[end], i)
	}

	removed := make(map[int]bool)

	for i := 0; i < len(lines); i++ {
		if removed[i] {
			continue
		}
		for j := i + 1; j < len(lines); j++ {
			if removed[j] {
				continue
			}
			for k := j + 1; k < len(lines); k++ {
				if removed[k] {
					continue
				}
				points := make(map[Point]int)
				edges := [3]int{i, j, k}
				for _, idx := range edges {
					p1 := toPoint(lines[idx][0])
					p2 := toPoint(lines[idx][1])
					points[p1]++
					points[p2]++
				}

				if len(points) == 3 {
					valid := true
					for _, count := range points {
						if count != 2 {
							valid = false
							break
						}
					}
					if valid {
						// Extract the three unique points
						var trianglePoints [][]float32
						for point := range points {
							trianglePoints = append(trianglePoints, []float32{point[0], point[1]})
						}
						
						// Only remove if the triangle area is greater than 1
						if len(trianglePoints) == 3 && is_valid_triangle(trianglePoints[0], trianglePoints[1], trianglePoints[2]) {
							removed[i] = true
							removed[j] = true
							removed[k] = true
						}
					}
				}
			}
		}
	}



	var filtered [][][]float32
	for i, line := range lines {
		if !removed[i] {
			filtered = append(filtered, line)
		}
	}
	return filtered
}

func RemoveUnrelated(lines [][][]float32) [][][]float32 {
	if len(lines) <= 1 {
		return lines
	}

	// Helper function to check if a point lies on a line segment
	pointOnLine := func(point []float32, line [][]float32) bool {
		const eps = 0.001
		x, y := point[0], point[1]
		x1, y1 := line[0][0], line[0][1]
		x2, y2 := line[1][0], line[1][1]

		// Check if point is exactly one of the endpoints
		if (math.Abs(float64(x-x1)) < eps && math.Abs(float64(y-y1)) < eps) ||
		   (math.Abs(float64(x-x2)) < eps && math.Abs(float64(y-y2)) < eps) {
			return true
		}

		// Check if point lies on the line segment
		// First check if point is collinear with the line
		crossProduct := (y-y1)*(x2-x1) - (x-x1)*(y2-y1)
		if math.Abs(float64(crossProduct)) > eps {
			return false // Not collinear
		}

		// Check if point is within the line segment bounds
		minX, maxX := x1, x2
		if minX > maxX {
			minX, maxX = maxX, minX
		}
		minY, maxY := y1, y2
		if minY > maxY {
			minY, maxY = maxY, minY
		}

		return x >= minX-float32(eps) && x <= maxX+float32(eps) && 
		       y >= minY-float32(eps) && y <= maxY+float32(eps)
	}

	var filtered [][][]float32

	for i, currentLine := range lines {
		startPoint := currentLine[0]
		endPoint := currentLine[1]
		
		startOnOtherLine := false
		endOnOtherLine := false

		// Check if both endpoints lie on any other line
		for j, otherLine := range lines {
			if i == j {
				continue // Skip the same line
			}

			if !startOnOtherLine && pointOnLine(startPoint, otherLine) {
				startOnOtherLine = true
			}
			if !endOnOtherLine && pointOnLine(endPoint, otherLine) {
				endOnOtherLine = true
			}

			// Early exit if both points are found on other lines
			if startOnOtherLine && endOnOtherLine {
				break
			}
		}

		// Keep the line only if both endpoints lie on other lines
		if startOnOtherLine && endOnOtherLine {
			filtered = append(filtered, currentLine)
		}
	}

	return filtered
}

func RemoveOuterRectangle(lines [][][]float32) [][][]float32 {
	if len(lines) == 0 {
		return lines
	}

	xmin, ymin, xmax, ymax := GetBoundingBox(lines)
	const eps = 0.001
	
	isApprox := func(a, b float32) bool {
		return math.Abs(float64(a-b)) < eps
	}
	
	isOnBoundary := func(line [][]float32) bool {
		x1, y1 := line[0][0], line[0][1]
		x2, y2 := line[1][0], line[1][1]
		
		if isApprox(x1, xmin) && isApprox(x2, xmin) {
			return true
		}
		
		if isApprox(x1, xmax) && isApprox(x2, xmax) {
			return true
		}
		
		if isApprox(y1, ymax) && isApprox(y2, ymax) {
			return true
		}
		
		if isApprox(y1, ymin) && isApprox(y2, ymin) {
			return true
		}
		
		return false
	}
	
	var filtered [][][]float32
	for _, line := range lines {
		if !isOnBoundary(line) {
			filtered = append(filtered, line)
		}
	}
	
	return filtered
}

