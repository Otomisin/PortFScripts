library(shiny)
library(shinydashboard)
library(dplyr)
library(tidyr)
library(ggplot2)
library(leaflet)
library(sf)
library(DT)
library(RColorBrewer)
library(shinyjs)
library(leaflet.extras)
library(stringr)
library(highcharter)
library(reactable)
library(shinyWidgets)
library(plotly)

# setwd("/Web_Site/Interactive_Map/Interactive_map_github")

# Relative paths to the GeoPackage files within the project directory
live_plants_path <- "data/Live_Plants.gpkg"
# box_area_path <- "data/Box_area.gpkg"
box_area_path <- "data/Box_area.json"


# Load the data
ssd_mt_admin_point_exp_N <- st_read(live_plants_path)

# Define the original column names
original_colnames <- c("SN", "New_Names", "Square Box", "Matched_Names", "Matched_Checks", 
                       "Vernacular Name", "Botanical_", "no_name", "Family", "Plant Category", 
                       "Life_Cycle", "Category", "Ecology", "Parts_Used", "Medicinal_", 
                       "Area_of_Or", "Local Applications", "Scientific research", "Notes")

# Assign these original names to the sf object, except for the geometry column
colnames(ssd_mt_admin_point_exp_N)[1:length(original_colnames)] <- original_colnames

SSD_Admin <- st_read(box_area_path)


# Drop the Z dimension
SSD_Admin <- st_zm(SSD_Admin)
# Convert sf object to Spatial
SSD_Admin_sp <- as(SSD_Admin, "Spatial")
bbox <- st_bbox(SSD_Admin)

SSD_Admin_sp <- as(SSD_Admin, "Spatial")
bbox <- st_bbox(SSD_Admin)

ssd_mt_admin_point_exp_N <- ssd_mt_admin_point_exp_N %>%
  mutate(id = row_number())

ssd_mt_admin_point_exp_N <- ssd_mt_admin_point_exp_N |>  
  rename(geometry = geom)

## Create CSS  -------------
css <- "


/* Change the box header background and text color */
.box.box-primary {
  border-top-color: #2c5444 !important; /* Change border top color */
  border-left-color: #2c5444 !important; /* Change border left color */
  border-right-color: #2c5444 !important; /* Change border right color */
  border-bottom-color: #2c5444 !important; /* Change border bottom color */
}

.box.box-primary > .box-header {
  background-color: #2c5444 !important; /* Ensure header background color is applied */
  color: white !important; /* Ensure the text color is white */
  border-bottom-color: #2c5444 !important; /* Match the bottom border to the header color */
}

.box.box-primary > .box-header .box-title {
  color: white !important; /* Ensure the title text color is white */
}

.box {
  border-color: #2c5444 !important; /* Change all borders of the box to match the header color */
}



/* Change the box header background and text color */
.box.box-primary {
  border-top-color: #2c5444; /* Your desired border color */
}

.box.box-primary > .box-header {
  background-color: #2c5444 !important; /* Use !important to override any other styles */
  color: white !important; /* Ensure the text color is white */
}

.box.box-primary > .box-header .box-title {
  color: white !important; /* Ensure the title text color is white */
}



## Top menu Bar ------------
/* Change the top header color */
.skin-blue .main-header .navbar {
  background-color: #2c5444; /* Replace with your desired color */
}

/* Change the top header text color */
.skin-blue .main-header .logo {
  background-color: #2c5444; /* Replace with your desired color */
  color: white; /* Replace with your desired text color */
}

/* Optionally change the sidebar color as well */
.skin-blue .main-sidebar {
  background-color: #2c5444; /* Replace with your desired sidebar color */
}

/* Change the sidebar menu item hover color */
.skin-blue .main-sidebar .sidebar .sidebar-menu > li.active > a,
.skin-blue .main-sidebar .sidebar .sidebar-menu > li:hover > a {
  background-color: #0a2d2e; /* Replace with your desired hover color */
}
/* Change the hover color for the top header */
.skin-blue .main-header .navbar:hover {
  background-color: #0a2d2e; /* Replace with your desired hover color */
}

/* Change the hover color for the sidebar menu items */
.skin-blue .main-sidebar .sidebar .sidebar-menu > li:hover > a {
  background-color: #0a2d2e; /* Replace with your desired hover color */
  color: white; /* Text color on hover */
}

/* Ensure the hover state for the entire navbar is consistent */
.skin-blue .main-header .navbar:hover,
.skin-blue .main-header .logo:hover {
  background-color: #0a2d2e; /* Ensure it remains the same color on hover */
  color: white; /* Ensure text color remains white on hover */
}

/* Ensure the hover state for the entire navbar and icon is consistent */
.skin-blue .main-header .navbar:hover,
.skin-blue .main-header .logo:hover,
.skin-blue .main-header .navbar .navbar-custom-menu .navbar-nav > li > a:hover {
  background-color: #0a2d2e; /* Ensure it remains the same color on hover */
  color: white; /* Ensure text and icon color remains white on hover */
}


## Plant Data Table Box ---------
/* Change the box header background and text color */
.box.box-primary {
  border-top-color: #2c5444; /* Replace with your desired color for the top border */
}

.box.box-primary > .box-header {
  background-color: #2c5444; /* Replace with your desired header background color */
  color: white; /* Replace with your desired header text color */
}

/* Change the box body background color */
.box.box-primary > .box-body {
  background-color: #F0F0F0; /* Replace with your desired body background color */
  color: #2c5444; /* Replace with your desired body text color */
}

/* Optional: Adjust the border of the box */
.box {
  border: 1px solid ##2c5444; /* Replace with your desired border color */
}


## Menu bars ----------
input[type='number'] {
  max-width: 80%;
}

/* Change the header color */
.skin-blue .main-header .navbar {
  background-color: #2c5444; /* Replace with your desired color */
}

/* Change the sidebar color */
.skin-blue .main-sidebar {
  background-color: #2c5444; /* Replace with your desired color */
}

/* Change the sidebar menu item hover color */
.skin-blue .main-sidebar .sidebar .sidebar-menu > li.active > a,
.skin-blue .main-sidebar .sidebar .sidebar-menu > li:hover > a {
  background-color: #0a2d2e; /* Replace with your desired color */
}


#row-description-container {
  position: absolute;
  top: 60px;
  right: 10px;
  width: 20%;  /* Adjust the width as needed */
}

div.outer {
  position: fixed;
  top: 41px;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  padding: 0;
}

body, label, input, button, select { 
  font-family: 'Helvetica Neue', Helvetica;
  font-weight: 200;
  background-color: #fdf6e8;
  color: #2c5444;
}

h1, h2, h3, h4 { 
  font-weight: 400;
  color: #2c5444;
}

#controls {
  background-color: #fdf6e8;
  padding: 0 20px 20px 20px;
  cursor: move;
  opacity: 0.85;
  zoom: 0.9;
  transition: opacity 500ms 1s;
  border: 1px solid #2c5444;
}
#controls:hover {
  opacity: 0.95;
  transition-delay: 0;
}

#cite {
  position: absolute;
  bottom: 10px;
  left: 10px;
  font-size: 12px;
}

.leaflet-container {
  background-color: #E6EFFB !important;
}

.green-popup .leaflet-popup-content-wrapper {
  background-color: #2c5444 !important;
  color: white;
}

.green-popup .leaflet-popup-tip-container {
  visibility: visible;
}

.marker-cluster-small, .marker-cluster-medium, .marker-cluster-large {
  color: white;
  text-align: center;
  font-size: 12px;
  line-height: 40px;
}
.marker-cluster-small div, .marker-cluster-medium div, .marker-cluster-large div {
  background-color: #2c5444;
  border: 2px solid #2c5444;
  border-radius: 20px;
}

/* Custom Legend Styling */
.custom-legend {
  background: white;
  padding: 10px;
  border-radius: 5px;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.2);
  width: 200px;  /* Fixed width for the legend */
}

.custom-legend .legend-title {
  font-weight: bold;
  margin-bottom: 5px;
  font-size: 14px;
}

.custom-legend .legend-scale ul {
  margin: 0;
  padding: 0;
  list-style: none;
}

.custom-legend .legend-scale ul li {
  display: inline-block;
  width: 50%;
  margin: 0;
}

.custom-legend .legend-scale ul li span {
  display: block;
  height: 12px;
  width: 12px;
  margin-right: 5px;
  float: left;
}

.custom-legend .legend-labels {
  display: flex;
  flex-wrap: wrap;
}

.custom-legend .legend-labels li {
  display: flex;
  align-items: center;
  width: 50%;
  font-size: 12px;
  margin-bottom: 5px;
}
"


## Rename Columns ------
ssd_mt_admin_point_exp_N <- ssd_mt_admin_point_exp_N %>%
  filter(is.na(Has_Orquídea_bromeliads)) |> 
  select(-SN, -`Square Box`, -Matched_Names, -no_name, -Life_Cycle, -Matched_Checks, -geometry, -
           Has_Orquídea_bromeliads) %>%
  rename(Plants = New_Names, `Botanical Names` = Botanical_,
         `Parts Used Medicinally` = Parts_Used,
         `Medical Use` = Medicinal_, Origin = Area_of_Or) |> 
  mutate(Category = str_to_title(Category))


categories <- sort(unique(ssd_mt_admin_point_exp_N$Category))
colors <- colorFactor(palette = brewer.pal(min(length(categories), 12), "Paired"), domain = categories)


## Create a separate data frame for the table --------
table_data <- ssd_mt_admin_point_exp_N %>%
  select(-any_of(c("SN", "Square Box", "Matched_Names", "no_name", "id",
                   "Life_Cycle", "Matched_Checks", "geometry", "image_url", "Notes", "Plant Category", "
Has_Orquídea_bromeliads"))) %>%
  st_drop_geometry() |> 
  rename(`Plant Category` = Category,
         `Scientific Research` = `Scientific research`)


# Column descriptions with detailed analysis
column_descriptions <- data.frame(
  Column = c("Plants", "Vernacular Name", "Botanical Names", "Family", "Plant Category", "Category", "Ecology", "Parts Used Medicinally", "Medical Use", "Origin", "Local Applications", "Scientific Research"),
  Description = c(
    "Common or local name of the plant.",
    "Local or traditional names used in various regions.",
    "Scientific name of the plant (Genus and species).",
    paste0(
      "<p>The botanical family to which the plant belongs. The dataset includes 92 distinct plant families:</p>",
      "<ul>",
      "<li><b>Fabaceae</b> is the most prominent family, comprising <b>10.0%</b> of the total plants, with <b>120 species</b>. This indicates a significant representation, reflecting the family’s ecological importance and diversity.</li>",
      "<li><b>Rubiaceae</b> follows closely, making up <b>9.02%</b> of the dataset with <b>108 species</b>. This is another highly diverse family, often found in tropical regions.</li>",
      "<li><b>Euphorbiaceae</b> accounts for <b>8.1%</b> of the species, showcasing its broad distribution and varied uses, particularly in medicinal contexts.</li>",
      "<li>Other notable families include <b>Annonaceae</b> (<b>5.26%</b>) and <b>Solanaceae</b> (<b>4.68%</b>), each with substantial contributions, indicating their ecological and possibly economic significance. For more information, check this <a href='https://yakumamaylivepharmacy.org/the-reserve/'>link</a>.</li>",
      "</ul>"
    ),
    "Classification of the plant based on its growth form (e.g., shrub, tree, herb). The Tree category dominates with <b>662 species</b>, followed by Shrub (<b>165 species</b>) and Subshrub (<b>106 species</b>).",
    paste0(
      "<p>Broader classification related to plant use or characteristics:</p>",
      "<ul>",
      "<li>The majority of the plants (<b>57.3%</b>, <b>873 species</b>) are used for general medicinal purposes, highlighting the dataset’s strong emphasis on ethnobotany and traditional medicine.</li>",
      "<li><b>Medicinal food</b> (foods with health benefits) and plants used in <b>Pusanga</b> (a type of shamanic medicine) each represent about <b>12-13%</b> of the total, reflecting the cultural practices tied to these plants.</li>",
      "<li>A smaller percentage (<b>3.22%</b>, <b>49 species</b>) are identified as poisonous, which is critical for understanding both the risks and potential uses in controlled medicinal applications.</li>",
      "</ul>"
    ),
    paste0(
      "<p>The environment or habitat where the plant is typically found:</p>",
      "<ul>",
      "<li><b>Planted</b> species lead with <b>19.3%</b> of the species, indicating many of these plants are likely cultivated for specific purposes, such as agriculture, horticulture, or conservation.</li>",
      "<li><b>Wild</b> species represent <b>14.8%</b> of the dataset, which suggests a considerable portion of the plants are naturally occurring, emphasizing the importance of wild habitats.</li>",
      "<li><b>Power Plant</b> and <b>Social Use</b> categories also show substantial representation (<b>15.9%</b> and <b>11.8%</b> respectively), pointing to the diverse roles these plants play, from ecosystem services to social and cultural functions.</li>",
      "</ul>"
    ),
    paste0(
      "<p>Specific parts of the plant used for medicinal purposes:</p>",
      "<ul>",
      "<li><b>Leaves</b> are the most commonly used part for medicinal purposes, accounting for <b>25.1%</b> of the uses. This is typical in herbal medicine, where leaves are often harvested for their therapeutic properties.</li>",
      "<li><b>Bark</b> (<b>22.0%</b>) and <b>Fruit</b> (<b>17.5%</b>) are also frequently used, suggesting that these parts have significant traditional or documented uses in healing practices.</li>",
      "<li>Less commonly used parts include <b>Roots</b> (<b>8.73%</b>), <b>Stems</b> (<b>6.77%</b>), and <b>Flowers</b> (<b>3.14%</b>), with the <b>Whole Plant</b> being used in about <b>3.97%</b> of the cases.</li>",
      "</ul>"
    ),
    paste0(
      "<p>Traditional or documented medicinal uses of the plant:</p>",
      "<ul>",
      "<li>The majority of the plants (<b>57.3%</b>, <b>873 species</b>) are used for general medicinal purposes, highlighting the dataset’s strong emphasis on ethnobotany and traditional medicine.</li>",
      "<li><b>Medicinal food</b> (foods with health benefits) and plants used in <b>Pusanga</b> (a type of shamanic medicine) each represent about <b>12-13%</b> of the total, reflecting the cultural practices tied to these plants.</li>",
      "<li>A smaller percentage (<b>3.22%</b>, <b>49 species</b>) are identified as poisonous, which is critical for understanding both the risks and potential uses in controlled medicinal applications.</li>",
      "</ul>"
    ),
    paste0(
      "<p>Geographic region or origin of the plant. The dataset features plants from <b>26 distinct geographical areas</b>:</p>",
      "<ul>",
      "<li><b>Southern Tropical America</b> is the primary region of origin, represented by <b>529 species</b>.</li>",
      "</ul>"
    ),
    paste0(
      "<p>Whether the plant is used locally for medicinal purposes or other applications:</p>",
      "<ul>",
      "<li>A significant majority of the plants (<b>97.0%</b>, <b>1161 species</b>) have documented local applications, underlining the rich traditional knowledge embedded within this dataset.</li>",
      "<li>Only a small percentage of species (<b>1.75%</b>) are noted as having no local applications, while <b>1.0%</b> remain unknown (<b>UNK</b>), which may suggest gaps in documentation or research.</li>",
      "</ul>"
    ),
    paste0(
      "<p>Indicates if there is scientific research or studies related to the plant:</p>",
      "<ul>",
      "<li>An overwhelming <b>94.7%</b> of the plants have associated scientific research, indicating a strong interest in studying these species, possibly due to their medicinal, ecological, or economic value.</li>",
      "<li>A small proportion (<b>3.26%</b>) have no known scientific research, which may highlight areas for future study, while <b>2.01%</b> are noted explicitly as not having been researched, suggesting they are either understudied or not recognized in scientific literature.</li>",
      "</ul>"
    )
  ),
  stringsAsFactors = FALSE
)







## UI Components --------
header <- dashboardHeader(
  title = "Yakumay Plant Base",
  titleWidth = 350
)

sidebar <- dashboardSidebar(
  width = 250,
  sidebarMenu(
    id = 'sidebar',
    menuItem("Table", tabName = 'dashboard', icon = icon('dashboard')),
    menuItem("Interactive Map", tabName = 'map', icon = icon('map')),
    menuItem("Analysis", tabName = 'analysis', icon = icon('bar-chart')),
    menuItem("FAQs", tabName = 'help', icon = icon('question-circle'))
  )
)

body <- dashboardBody(
  tabItems(
    tabItem(tabName = 'dashboard',
            h2("Welcome to the Yakumay Plant Dashboard"),
            HTML("Search plants by their common names, botanical names, families, and categorizations.<br>
Discover information about their ecological requirements, medicinal properties, geographic origins, and traditional uses in local communities.<br>
Read more about the categories <a href='https://yakumamaylivepharmacy.org/the-reserve/' target='_blank'>here</a>."),
            # p("You can go to the interactive map here:", actionLink("go_to_map", "Interactive Map")),
            fluidRow(
              valueBoxOutput("totalPlantsBox"),
              valueBoxOutput("uniqueFamiliesBox"),
              valueBoxOutput("originRegionsBox")
            ),
            fluidRow(
              box(
                title = tags$span(style = "color: white; background-color: #2c5444;", "Plant Data Table"), 
                width = 12, 
                solidHeader = TRUE, 
                status = "primary",
                reactableOutput("table")
              )
              
            ),
            fluidRow(
              box(
                width = 12, solidHeader = TRUE,
                p(tags$em(
                  "Additional information on the classifications can be found ",
                  a("here", href = "https://yakumamaylivepharmacy.org/the-reserve/", target = "_blank")
                ))
              )
            )
    ),
    
    tabItem(tabName = 'map',
            fluidRow(
              useShinyjs(),
              div(class = "outer",
                  tags$head(
                    tags$style(HTML(css)),
                    tags$script(HTML("
                  Shiny.addCustomMessageHandler('leaflet-zoom-resize', function(message) {
                    var map = $('#map').data('leaflet-map');
                    if (map) {
                      map.on('zoomend', function() {
                        var currentZoom = map.getZoom();
                        var newRadius = currentZoom * 1.5;
                        map.eachLayer(function(layer) {
                          if (layer.options && layer.options.radius) {
                            layer.setRadius(newRadius);
                          }
                        });
                      });
                    }
                  });
                "))
                  ),

                  leafletOutput("map", width = "100%", height = "100%"),
                  absolutePanel(id = "controls", class = "panel panel-default", fixed = TRUE,
                                draggable = TRUE, top = 95, left = 300, right = "auto", bottom = "auto",
                                width = 330, height = "auto",
                                h2("Filter Plants"),
                                
                                pickerInput("growth_form", "Growth Form Category", 
                                            choices = c("All" = "All", 
                                                        setNames(unique(na.omit(ssd_mt_admin_point_exp_N$Category)), 
                                                                 unique(na.omit(ssd_mt_admin_point_exp_N$Category)))),
                                            selected = "All",
                                            options = list(`actions-box` = TRUE), 
                                            multiple = TRUE),
                                
                                textInput("search", "Search Plant Name", value = ""),
                                
                                div(id = "plant_info", style = "margin-top: 20px;")
                  )
              )
            ),
            div(id = "row-description-container", uiOutput("rowDescription"))
    ),
    
    
    tabItem(tabName = 'analysis',
            fluidRow(
              # Row 1: Tree Map Analysis box and tree map output
              column(width = 4,
                     box(title = "Tree Map Analysis", width = NULL, 
                         style = "height: 250px; overflow-y: auto;", 
                         selectInput("treeMapColumn", "Select Column for Tree Map:",
                                     choices = c("Family", 
                                                 "Plant Category", 
                                                 "Ecology", 
                                                 "Parts Used Medicinally", 
                                                 "Medical Use", 
                                                 "Origin", 
                                                 "Local Applications", 
                                                 "Scientific Research"),
                                     selected = "Parts Used Medicinally")
                     ),
                     box(
                       width = NULL,
                       style = "height: 375px; margin-top: 0;",  # Ensure no space between boxes
                       uiOutput("columnDescription")
                     )
              ),
              column(width = 8,
                     box(width = NULL,
                         highchartOutput("tree_map", height = "670px")  # Tree map output
                     )
              )
            ),
            fluidRow(
              column(width = 12,
                     box(width = NULL,
                         
                         uiOutput("columnDescription1")  # New text output for column description
                     )
              )
            )
    )
    
    
    
    
    
    
    
    
    
    ,
    
    tabItem(tabName = 'help',
            h2(strong("FAQs")),
            p("Frequently asked questions about the dashboard and the data."),
            br(),
            
            h4(strong("1. What is the Yakumay Plant Base Dashboard?")),
            p(em("The Yakumay Plant Base Dashboard is an interactive tool designed to help users explore, analyze, and understand various plant species. It includes information on plant names, medicinal uses, origins, and other botanical characteristics.")),
            br(),
            
            h4(strong("2. How do I use the interactive map?")),
            p(em("You can use the interactive map to locate plants geographically. The map allows you to filter plants based on their growth form category or search for specific plants by name. Simply use the controls on the map to zoom in, filter, and explore plant data.")),
            br(),
            
            h4(strong("3. What data is available in the Plant Data Table?")),
            p(em("The Plant Data Table provides a comprehensive view of the available plant data, including common names, botanical names, parts used medicinally, medicinal uses, and origins. You can filter, search, and sort the data within the table.")),
            br(),
            
            h4(strong("4. What is the Tree Map Analysis used for?")),
            p(em("The Tree Map Analysis allows users to visualize the distribution of plants based on various categories such as family, ecology, and medicinal uses. This helps in understanding the distribution and significance of different plant categories.")),
            br(),
            
            h4(strong("5. How do I search for specific plants in the dashboard?")),
            p(em("You can search for specific plants using the search box provided in the Interactive Map section. Just enter the plant name, and the map will highlight the locations where that plant is found.")),
            br(),
            
            h4(strong("6. Where can I find additional information on plant classifications?")),
            p(HTML("<em>Additional information on plant classifications can be found on our official website: <a href='https://yakumamaylivepharmacy.org/the-reserve/' target='_blank'>Yakumay Live Pharmacy</a>.</em>")),
            br(),
            
            h4(strong("7. Can I download the data from the dashboard?")),
            p(em("Currently, the dashboard does not support direct data downloads. However, you can manually copy data from the table or screenshot the visualizations for your use.")),
            br(),
            
            h4(strong("8. Who can I contact for more information?")),
            p(em("For further inquiries or detailed information, please contact the support team through the official website contact page."))
    )
    
    
    
  )
)

ui <- dashboardPage(header, sidebar, body)

## Server Logic
server <- function(input, output, session) {
  filtered_data <- reactive({
    data <- ssd_mt_admin_point_exp_N
    if (!("All" %in% input$growth_form)) {
      data <- data %>% filter(Category %in% input$growth_form)
    }
    if (input$search != "") {
      data <- data %>% filter(grepl(input$search, Plants, ignore.case = TRUE))
    }
    data
  })
  
  
  filtered_categories <- reactive({
    unique(filtered_data()$Category)
  })
  
  updateSelectizeInput(session, 'search', choices = unique(ssd_mt_admin_point_exp_N$Plants), server = TRUE)
  
  observeEvent(input$go_to_map, {
    updateTabItems(session, "sidebar", "map")
  })
  
  # Custom cluster options with gradient color
  cluster_options <- markerClusterOptions(
    iconCreateFunction = JS("
      function (cluster) {
        var childCount = cluster.getChildCount();
        var c = ' marker-cluster-';

        if (childCount < 10) {
          c += 'small';
        } else if (childCount < 100) {
          c += 'medium';
        } else {
          c += 'large';
        }

        var color = '#2c5444';
        if (childCount >= 10 && childCount < 100) {
          color = '#1e3b2e';  // Darker shade for medium clusters
        } else if (childCount >= 100) {
          color = '#0f1e17';  // Darkest shade for large clusters
        }

        return new L.DivIcon({ 
          html: '<div style=\"background-color:' + color + ';\"><span>' + childCount + '</span></div>', 
          className: 'marker-cluster' + c, 
          iconSize: new L.Point(40, 40),
          iconAnchor: new L.Point(20, 20)
        });
      }
    ")
  )
  
  output$map <- renderLeaflet({
    valid_SSD_Admin <- SSD_Admin[!is.na(SSD_Admin$geometry), ]
    
    leaflet(options = leafletOptions(minZoom = 0, maxZoom = 30)) %>%
      addTiles(group = "OSM") %>%
      addProviderTiles("CartoDB.Positron", group = "Carto Basemap") %>%
      
      addPolygons(data = valid_SSD_Admin,
                  color = "grey",
                  weight = 2,
                  opacity = 0.05,
                  fillColor = "#ffffff",
                  fillOpacity = 0.2,
                  highlightOptions = highlightOptions(color = "#2c5444", weight = 5,
                                                      bringToFront = FALSE),
                  group = "Polygon") %>%
      
      addCircleMarkers(data = filtered_data(),
                       layerId = ~id,
                       color = ~colors(Category),
                       fillColor = ~colors(Category),
                       radius = 3,
                       stroke = TRUE,
                       fillOpacity = 0.8,
                       label = ~Plants,
                       popup = ~paste("<div style='display: flex; flex-direction: column;'>",
                                      "<div style='display: flex; align-items: center; justify-content: space-between; width: 100%;'>",
                                      "<span style='font-size: 20px;'><b>", toupper(Plants), "</b></span>",
                                      # "<img src='www/plant_image.png' style='width: 100px; height: auto; margin-left: 10px;'>",
                                      "</div>",
                                      "<hr style='margin: 10px 0;'>",
                                      "<div><b>BOTANICAL NAME: </b><i>", `Botanical Names`, "</i></div>",
                                      "<div><b>ORIGIN: </b>", Origin, "</div>",
                                      "</div>"),
                       labelOptions = labelOptions(
                         style = list("font-weight" = "normal", 
                                      "font-family" = "serif", 
                                      "padding" = "3px 8px",
                                      "color" = "#2c5444",
                                      "box-shadow" = "3px 3px rgba(0,0,0,0.25)", 
                                      "border-color" = "rgba(0,0,0,0.5)",
                                      "background-color" = "rgba(255, 255, 255, 0.5)",
                                      "opacity" = "0.1"),
                         textsize = "15px",
                         direction = "auto"),
                       popupOptions = popupOptions(
                         closeButton = TRUE,
                         className = "green-popup"
                       ),
                       clusterOptions = cluster_options,
                       group = "Plants") %>%
      addControl(html = createCustomLegend(filtered_categories(), colors), position = "bottomright")
  })
  
  observeEvent(input$map_marker_click, {
    click <- input$map_marker_click
    plant <- filtered_data() %>% filter(id == click$id)
    if (nrow(plant) == 1) {
      plant_info <- paste("<hr>",'<span style="font-size: 20px;"><b>', toupper(plant$Plants), '</b></span>',
                          "<hr>",
                          "<b>BOTANICAL NAME: </b><i>", plant$`Botanical Names`, "</i><br>",
                          "<b>MEDICINAL USE: </b>", plant$`Medical Use`, "<br>",
                          "<b>PARTS USED MEDICALLY: </b>", plant$`Parts Used Medicinally`, "<br>",
                          "<b>ORIGIN: </b>", plant$Origin, "<br>",
                          "<b>ADDITIONAL NOTES: </b><i>", plant$Notes, "</i><br>")
      shinyjs::html("plant_info", plant_info)
    }
  })
  
  # Tree Map Analysis UI and Plot Rendering Logic
  output$tree_map <- renderHighchart({
    req(input$treeMapColumn)  # Ensure the input is available

    tree_map_data <- table_data %>%
      separate_rows(!!sym(input$treeMapColumn), sep = ",") %>%  # Split multiple parts
      mutate_at(vars(input$treeMapColumn), str_trim) %>%  # Trim whitespace
      mutate_at(vars(input$treeMapColumn), str_to_title) %>%  # Trim whitespace
      count(!!sym(input$treeMapColumn)) %>%   # Count occurrences
      rename(name = !!sym(input$treeMapColumn), value = n) |>   # Rename columns for highcharter
    # rename(name = `Scientific Research`, value = n)
    arrange(desc(value))
    
    
    # Ensure that the data is not empty
    if (nrow(tree_map_data) == 0) {
      showNotification("No data available for tree map", type = "error")
      return(NULL)
    }
    
    # Dynamically generate a color gradient with darker colors for higher values
    num_colors <- nrow(tree_map_data)
    color_palette <- colorRampPalette(c("#2c5444", "#a3c293"))(num_colors)  # From dark green to light green
    
    # Create the tree map with green colors in descending order
    highchart() %>%
      hc_add_series(
        type = "treemap",
        data = list_parse2(tree_map_data),
        layoutAlgorithm = "squarified",
        colorByPoint = TRUE,  # Applies different colors to each point
        colors = color_palette,  # Use dynamically generated green shades
        levels = list(
          list(
            level = 1,
            dataLabels = list(enabled = TRUE),
            borderWidth = 3
          )
        )
      ) %>%
      hc_title(text = paste("Distribution of", input$treeMapColumn)) %>%
      hc_tooltip(pointFormat = "<b>{point.name}</b>: {point.value}")
  })
  
  
  
  
  
  
  # Reactive expression for the selected row description
  
  output$rowDescription <- renderUI({
    tagList(
      HTML("<h3 style='z-index: 1000; background-color: #2c5444; color: white; padding: 10px; border-radius: 5px;'>Welcome to Yakumay Plant Interactive Map</h3>"),
      HTML("<b>Note:</b> Use the filter and search functions to investigate the spatial distribution of plants. 
    The automatic clustering feature identifies groups of plants located close together. Numbers on the live map indicate the number of plants within a specific cluster. 
         <b>Hovering</b> over a number reveals the cluster's shape, and zooming in provides a detailed view of the individual plants.")
    )
  })
  
  
  # Reactive expression for the selected column description
  output$columnDescription <- renderUI({
    selected_column <- input$treeMapColumn
    description <- column_descriptions %>%
      filter(Column == selected_column) %>%
      pull(Description)
    
    HTML(paste0("<b>", selected_column, ":</b> ", description))
  })
  
  output$columnDescription1 <- renderUI({
    HTML("<p> <strong>NOTE:</strong> The above analysis excludes orchids and bromeliads that were recorded in the survey, but no information was gathered about them. 
         <br>For more information on the various categories, check this <a href='https://yakumamaylivepharmacy.org/the-reserve/'>link</a>.</p>")
  })
  
  
  
##Output table
  output$table <- renderReactable({
    reactable(
      table_data,
      filterable = TRUE,
      searchable = TRUE,
      pagination = TRUE,
      defaultSortOrder = "asc",
      defaultPageSize = 20,
      highlight = TRUE,
      bordered = TRUE,
      striped = TRUE,
      resizable = TRUE,
      defaultSorted = c("Vernacular Name"),
      columns = list(
        `Botanical Names` = colDef(
          style = list(fontStyle = "italic")
        ),
        `Vernacular Name` = colDef(defaultSortOrder = "asc"),
        Plants = colDef(show = FALSE)
      ),
      theme = reactableTheme(
        borderColor = "#dfe2e5",
        stripedColor = "#f6f8fa",
        highlightColor = "#f0f5f9",
        cellPadding = "8px 12px",
        style = list(fontFamily = "-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif"),
        searchInputStyle = list(width = "100%")
      )
    )
  })
  
  ## Analysis Section Logic ------
  output$totalPlantsBox <- renderValueBox({
    valueBox(
      nrow(table_data), "Total Plants", icon = icon("leaf"),
      color = "olive"
    )
  })
  
  output$uniqueFamiliesBox <- renderValueBox({
    valueBox(
      length(unique(table_data$Family)), "Unique Families", icon = icon("tree"),
      color = "orange"
    )
  })
  
  output$originRegionsBox <- renderValueBox({
    valueBox(
      length(unique(table_data$Origin)), "Regions of Origin", icon = icon("globe"),
      color = "maroon"
    )
  })
  
  # Send a custom message to initialize the marker resizing functionality
  session$sendCustomMessage(type = 'leaflet-zoom-resize', message = list())
}

# Create Custom Legend
createCustomLegend <- function(categories, colors) {
  sorted_categories <- sort(categories)
  labels <- paste0("<li><span style='background:", colors(sorted_categories), ";'></span>", sorted_categories, "</li>")
  legend_html <- paste0("
    <div class='custom-legend'>
      <div class='legend-title'>Plant Category</div>
      <div class='legend-scale'>
        <ul class='legend-labels'>", paste(labels, collapse = ""), "</ul>
      </div>
    </div>")
  return(legend_html)
}

# Run the application
shinyApp(ui, server)
