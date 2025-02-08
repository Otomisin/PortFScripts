library(shiny)
library(leaflet)
library(rsconnect)
library(sf)

# rsconnect::deployApp("./ClickEvent_SSD.R")

# setwd("./Interactive_mapShiny")
ssd_mt_admin_point_exp_N <-st_read("./ssd_mt_admin_point_exp_N.gpkg")
SSD_Admin <- st_read("./SSD_Admin.gpkg")


# Get Bounding box
library(rnaturalearth)

# Get the shapefile for Nigeria
SSD_shapefile <- ne_countries(country = "South Sudan", returnclass = "sf")

# Extract bounding coordinates
bbox <- st_bbox(SSD_shapefile)

# Get individual coordinates
min_long <- bbox$xmin
max_long <- bbox$xmax
min_lat <- bbox$ymin
max_lat <- bbox$ymax


ui <- bootstrapPage(
  tags$style(type = "text/css", "html, body { width:100%; height:100%; }"),
  leafletOutput("myMap", width= "100%", height = "95%"),  # Reduce the map height to make space for the button
  tags$style(HTML("
    .blue-popup .leaflet-popup-content-wrapper {
      background-color: #0033A0;
      color: white;
    }
  ")),
  # Absolute panel will house the user input widgets
  absolutePanel(top = 10, right = 10, fixed = TRUE,
                tags$div(style = "opacity: 0.70; background: #FFFFEE; padding: 8px;",
                         actionButton("exportMapBtn", "Export Map")  # Add the Export Map button
                )
  )
)

server <- function(input, output, session) {
  output$myMap <- renderLeaflet({
    leaflet(options = leafletOptions(minZoom = 0, maxZoom = 18)) %>%
      # addTiles(group = "OSM (default)") %>%
      addProviderTiles("Esri.WorldGrayCanvas", group = "Esri_Basemap") %>%
      addProviderTiles("CartoDB.Positron", group = "Carto_Basemap") %>%
      addPolygons(data = SSD_Admin,
                  label = ~ADM3_NAME_,
                  popup = ~paste('<span style="font-size: 15px;"><b>', "ATTRIBUTES", '</b></span>',
                                 "<hr>",
                                 "County: ", ADM2_EN_18,
                                 "<br>", "Payam : ", ADM3_NAME_,
                                 "<br>", "PCODE: ", Payam_MT_P),
                  color = "grey",
                  weight = 2,
                  fillColor = "#E6EFFB",
                  labelOptions = labelOptions(
                    style = list("font-weight" = "normal", padding = "3px 8px"),
                    textsize = "15px",
                    direction = "auto"),
                  dashArray = "3",
                  fillOpacity = .2,
                  highlightOptions = highlightOptions(color = "#0033A0", weight = 5,
                                                      bringToFront = FALSE),
                  group = "Payam",
                  popupOptions = popupOptions(
                    closeButton = TRUE, # Optional, set to TRUE to enable a close button
                    className = "blue-popup" # Add a custom class for styling
                  )
                  ) |>
      addCircleMarkers(data = ssd_mt_admin_point_exp_N,
                       color = ifelse(ssd_mt_admin_point_exp_N$Others_payam == "yes", "orange", "#4066B8"),
                       fillColor = ifelse(ssd_mt_admin_point_exp_N$Others_payam == "yes", "orange", "#4066B8"),
                       radius = 7,
                       stroke = TRUE,
                       fillOpacity = 0.8,
                       popup = ~paste("Code4Form |", A7_payam_form),
                       group = "marker") |>
      addLegend(position = "bottomleft",
                colors = c("#4066B8", "orange"),
                labels = c("No", "Yes "),  # Add labels for the colors here
                opacity = 1,
                title = "New Sites") |>
      addMeasure(
        position = "bottomleft",
        primaryLengthUnit = "meters",
        primaryAreaUnit = "sqmeters",
        activeColor = "#3D535D",
        completedColor = "#7D4479") |>
      addMiniMap(
        tiles = providers$Esri.WorldStreetMap,
        toggleDisplay = TRUE) |>
      addLayersControl(baseGroups = c("Carto_Basemap", "Esri_Basemap" ),
                       overlayGroups = c("marker", "Payam"),
                       option = layersControlOptions(collapsed = FALSE)
      ) |>
      fitBounds(lng1 = 29,lat1 = 4.852 ,lng2 = 32,lat2 = 11, options = list(zoom_level=3))
    # fitBounds(lng1 = 25,lat1 = 2 ,lng2 = 35,lat2 = 13, options = list(zoom_level=1))
  })
  # addPopups
  #
  # min_long <- bbox$xmin
  # max_long <- bbox$xmax
  # min_lat <- bbox$ymin
  # max_lat <- bbox$ymax

  # observe(
  #   {  click = input$myMap_shape_click
  #   if(is.null(click))
  #     return()
  #   else
  #     leafletProxy("myMap") %>%
  #     setView(lng = click$lng , lat = click$lat, zoom = 11)
  #
  #   }
  #
  # )

  ## Double click event
  observeEvent(input$myMap_dblclick, {
    click <- input$myMap_dblclick
    if (is.null(click))
      return()
    else
      leafletProxy("myMap") %>%
      setView(lng = click$lng, lat = click$lat, zoom = 15)
  })


}

shinyApp(ui, server)
