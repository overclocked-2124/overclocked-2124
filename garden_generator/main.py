import os
import requests
import svgwrite
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

GH_USERNAME = "overclocked-2124"
GH_TOKEN = os.getenv("GH_TOKEN_GARDEN") 

# --- Configuration ---
CELL_SIZE = 12
CELL_MARGIN = 2
YEAR_WIDTH_WEEKS = 53
DAYS_IN_WEEK = 7
IMAGE_PADDING = 20

COLOR_BACKGROUND = "#1a1b27"
COLOR_LEVEL_0 = "#2f3542"
COLOR_LEVEL_1 = "#3b6b4f"
COLOR_LEVEL_2 = "#5c9a73"
COLOR_LEVEL_3 = "#7ac08e"
COLOR_LEVEL_4 = "#9fd8aa"
TEXT_COLOR = "#a9b1d6"

# +++++++++ NEW HELPER FUNCTION +++++++++
def lighten_hex_color(hex_color, amount=0.3):
    """
    Lightens the given hex color by a specified amount.
    Amount should be between 0 (no change) and 1 (white).
    """
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        # Handle cases like shorthand hex if necessary, or return original if invalid
        # For now, assume valid 6-digit hex
        print(f"Warning: Invalid hex color format for lighten: {hex_color}")
        return f"#{hex_color}" # Return original or a default error color

    try:
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        print(f"Warning: Could not parse hex to RGB: {hex_color}")
        return f"#{hex_color}" # Return original or default


    new_rgb = []
    for val in rgb:
        new_val = int(val + (255 - val) * amount)
        new_rgb.append(min(max(0, new_val), 255))
        
    return "#%02x%02x%02x" % tuple(new_rgb)
# ++++++++++++++++++++++++++++++++++++++

# --- GitHub API Fetching --- (Keep as is)
def fetch_contribution_data(username, token):
    # ... (your existing function) ...
    today = datetime.utcnow().date()
    to_date = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    from_date = (today - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")

    query = """
    query($userName:String!, $from:DateTime!, $to:DateTime!) {
      user(login: $userName){
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
                weekday
              }
            }
          }
        }
      }
    }
    """
    variables = {"userName": username, "from": from_date, "to": to_date}
    headers = {"Authorization": f"bearer {token}"}
    response = None # Initialize response
    try:
        response = requests.post("https://api.github.com/graphql", json={"query": query, "variables": variables}, headers=headers)
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching contribution data: {e}")
        if response is not None:
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.text}")
        return None

# --- Plant Drawing Logic --- (get_plant_style as is)
def get_plant_style(count):
    # ... (your existing function) ...
    if count == 0:
        return {"fill": COLOR_LEVEL_0, "type": "seed"}
    elif count <= 2: 
        return {"fill": COLOR_LEVEL_1, "type": "sprout"}
    elif count <= 5:
        return {"fill": COLOR_LEVEL_2, "type": "stem"}
    elif count <= 9:
        return {"fill": COLOR_LEVEL_3, "type": "leaves"}
    else:
        return {"fill": COLOR_LEVEL_4, "type": "flower"}


def draw_day_cell(dwg, x, y, size, plant_style):
    cell_center_x = x + size / 2
    cell_center_y = y + size / 2
    
    if plant_style["type"] == "seed":
        dwg.add(dwg.circle(center=(cell_center_x, cell_center_y), r=size*0.1, fill=plant_style["fill"]))
    elif plant_style["type"] == "sprout":
        dwg.add(dwg.rect(insert=(x + size*0.4, y + size*0.6), size=(size*0.2, size*0.3), fill=plant_style["fill"]))
        dwg.add(dwg.circle(center=(cell_center_x, y + size*0.5), r=size*0.2, fill=plant_style["fill"]))
    elif plant_style["type"] == "stem":
        dwg.add(dwg.rect(insert=(x + size*0.4, y + size*0.3), size=(size*0.2, size*0.6), fill=plant_style["fill"]))
        dwg.add(dwg.circle(center=(cell_center_x, y + size*0.25), r=size*0.25, fill=plant_style["fill"]))
    elif plant_style["type"] == "leaves":
        dwg.add(dwg.rect(insert=(x + size*0.4, y + size*0.2), size=(size*0.2, size*0.7), fill=plant_style["fill"]))
        dwg.add(dwg.ellipse(center=(cell_center_x, y + size*0.4), r=(size*0.3, size*0.15), fill=plant_style["fill"]))
        dwg.add(dwg.circle(center=(cell_center_x, y + size*0.2), r=size*0.3, fill=plant_style["fill"]))
    elif plant_style["type"] == "flower":
        dwg.add(dwg.rect(insert=(x + size*0.4, y + size*0.1), size=(size*0.2, size*0.8), fill=plant_style["fill"]))
        dwg.add(dwg.circle(center=(cell_center_x, y + size*0.2), r=size*0.4, fill=plant_style["fill"]))
        
        # +++++++++ MODIFIED LINES +++++++++
        lighter_petal_color = lighten_hex_color(plant_style["fill"], 0.25) # Adjust lightness (e.g., 0.25 for 25% lighter)
        dwg.add(dwg.circle(center=(cell_center_x - size*0.2, y + size*0.15), r=size*0.2, fill=lighter_petal_color))
        dwg.add(dwg.circle(center=(cell_center_x + size*0.2, y + size*0.15), r=size*0.2, fill=lighter_petal_color))
        # +++++++++++++++++++++++++++++++++

# --- SVG Generation --- (generate_garden_svg as is)
def generate_garden_svg(data, output_path):
    # ... (your existing function) ...
    if not data or 'data' not in data or not data['data']['user'] or not data['data']['user']['contributionsCollection']: # Added check for contributionsCollection
        print("No valid contribution data or structure to generate garden.")
        dwg = svgwrite.Drawing(output_path, profile='tiny', 
                               size=(f"{YEAR_WIDTH_WEEKS * (CELL_SIZE + CELL_MARGIN) + 2*IMAGE_PADDING}px",
                                     f"{DAYS_IN_WEEK * (CELL_SIZE + CELL_MARGIN) + 2*IMAGE_PADDING + 30}px"))
        dwg.add(dwg.rect(insert=(0,0), size=('100%','100%'), fill=COLOR_BACKGROUND))
        error_text = "Could not load contribution data to generate garden."
        if data and 'errors' in data: # Check if GitHub API returned errors
             error_text = f"GitHub API Error: {data['errors'][0]['message'][:100]}" # Show first 100 chars of API error
        dwg.add(dwg.text(error_text, insert=(IMAGE_PADDING, IMAGE_PADDING + 20), fill=TEXT_COLOR, font_size="12px"))
        dwg.save()
        return

    calendar = data['data']['user']['contributionsCollection']['contributionCalendar']
    total_contributions = calendar['totalContributions']
    
    img_width = YEAR_WIDTH_WEEKS * (CELL_SIZE + CELL_MARGIN) - CELL_MARGIN + 2 * IMAGE_PADDING
    img_height = DAYS_IN_WEEK * (CELL_SIZE + CELL_MARGIN) - CELL_MARGIN + 2 * IMAGE_PADDING + 50 

    dwg = svgwrite.Drawing(output_path, size=(f"{img_width}px", f"{img_height}px"), profile='full')
    dwg.add(dwg.rect(insert=(0,0), size=('100%','100%'), fill=COLOR_BACKGROUND))

    title_el = dwg.text(f"{GH_USERNAME}'s Contribution Garden - Last Year ({total_contributions} Contributions)",
                      insert=(IMAGE_PADDING, IMAGE_PADDING + 15), 
                      fill=TEXT_COLOR, font_size="16px", font_family="Arial, sans-serif", font_weight="bold")
    dwg.add(title_el)
    
    grid_start_y = IMAGE_PADDING + 40 

    for week_idx, week in enumerate(calendar['weeks']):
        for day_info in week['contributionDays']:
            day_idx = day_info['weekday'] 
            
            x = IMAGE_PADDING + week_idx * (CELL_SIZE + CELL_MARGIN)
            y = grid_start_y + day_idx * (CELL_SIZE + CELL_MARGIN)
            
            count = day_info['contributionCount']
            plant_style = get_plant_style(count)
            
            draw_day_cell(dwg, x, y, CELL_SIZE, plant_style)

    dwg.save()
    print(f"Garden SVG saved to {output_path}")

# (main execution block as is)
if __name__ == "__main__":
    if not GH_TOKEN:
        # Try to fetch from environment again if it was missed by dotenv somehow in actions
        GH_TOKEN = os.environ.get("GH_TOKEN_GARDEN") 
        if not GH_TOKEN:
            raise ValueError("GH_TOKEN_GARDEN environment variable not set.")
    
    # Construct paths relative to the script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, '..', 'output') # Output dir is one level up from garden_generator

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    svg_path = os.path.join(output_dir, "contribution_garden.svg")

    contribution_data = fetch_contribution_data(GH_USERNAME, GH_TOKEN)
    generate_garden_svg(contribution_data, svg_path)
