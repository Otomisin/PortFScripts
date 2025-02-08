library(shiny)
library(dplyr)
library(rvest)
library(httr)
library(lubridate)
library(DT)
library(writexl)
library(shinyWidgets)

# Custom CSS
css <- "
input[type='number'] {
  max-width: 80%;
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

/* Customize fonts */
body, label, input, button, select { 
  font-family: 'Helvetica Neue', Helvetica;
  font-weight: 200;
  background-color: #F1F1F1;
  color: #040914;
}

h1, h2, h3, h4 { 
  font-weight: 400;
  color: #040914;
}

#controls {
  /* Appearance */
  background-color: #F1F1F1;
  padding: 0 20px 20px 20px;
  cursor: move;
  /* Fade out while not hovering */
  opacity: 0.85;
  zoom: 0.9;
  transition: opacity 500ms 1s;
  border: 1px solid #040914;
}
#controls:hover {
  /* Fade in while hovering */
  opacity: 0.95;
  transition-delay: 0;
}

/* Position and style citation */
#cite {
  position: absolute;
  bottom: 10px;
  left: 10px;
  font-size: 12px;
}

/* If not using map tiles, show a white background */
.leaflet-container {
  background-color: #E6EFFB !important;
}

.green-popup .leaflet-popup-content-wrapper {
  background-color: #040914 !important;
  color: white;
}

/* Ensure the popup arrow is visible */
.green-popup .leaflet-popup-tip-container {
  visibility: visible;
}

/* New styles with secondary color */
.dateRangeInput-container {
  color: #0834a4;
}

.selectize-control.single .selectize-input, 
.selectize-control.single .selectize-input input {
  background-color: #0834a4;
}

#download_data {
  background-color: #0834a4;
  border-color: #0834a4;
  color: white;
}

#download_data:hover {
  background-color: #0a4dcb;
  border-color: #0a4dcb;
}

/* Custom style for hr */
hr.custom-hr {
  border-top: 2px solid #040914;
}

hr.custom-hr_v2 {
  border-top: .001px solid #CCCED1;
}
"

# Initialize global cache variable
cached_data <- NULL

# Function to scrape data
scrape_data <- function(pages = 1) {
  base_url <- 'https://dtm.iom.int/reports'
  start_date <- as.Date("1970-01-01")
  
  # Initialize an empty data frame with the expected column names and types
  reports_data <- data.frame(
    Title = character(),
    Summary = character(),
    Link = character(),
    Published_Date = as.Date(character()),
    Country_Name = character(),
    Region = character(),
    Report_Type = character(),
    stringsAsFactors = FALSE
  )
  
  for (page in 0:(pages - 1)) {
    url <- ifelse(page == 0, base_url, paste0(base_url, "?page=", page))
    
    response <- httr::GET(url, httr::user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"))
    dtm_soup <- read_html(response)
    
    dtm_reports <- dtm_soup %>% html_nodes('.report-item1')
    
    for (report in dtm_reports) {
      title <- report %>% html_node('h5 a[hreflang]') %>% html_text(trim = TRUE)
      report_link <- report %>% html_node('h5 a[hreflang]') %>% html_attr('href')
      report_link <- ifelse(!is.na(report_link), paste0('https://dtm.iom.int', report_link), NA)
      date_info <- report %>% html_node('.date') %>% html_text() %>% strsplit('·') %>% unlist() %>% trimws()
      date <- ifelse(length(date_info) > 0, mdy(date_info[1]), NA)
      region <- ifelse(length(date_info) > 1, date_info[2], 'Unknown')
      country_name <- ifelse(length(date_info) > 2, date_info[3], 'Unknown')
      report_type <- ifelse(length(date_info) > 3, date_info[4], 'Unknown')
      summary_content <- report %>% html_node('.content') %>% html_text(trim = TRUE)
      
      reports_data <- rbind(reports_data, data.frame(
        Title = title,
        Summary = summary_content,
        Link = report_link,
        Published_Date = date,
        Country_Name = country_name,
        Region = region,
        Report_Type = report_type,
        stringsAsFactors = FALSE
      ))
    }
  }
  
  reports_data <- reports_data %>%
    mutate(Published_Date = start_date + as.numeric(Published_Date))
  
  return(reports_data)
}

# UI
ui <- fluidPage(
  tags$style(HTML(css)),  # Include custom CSS here
  sidebarPanel(
    h3(HTML("<strong style='color:#0834a4;'>About this App</strong>")),
    p("This dashboard provides an interactive way to explore reports published by IOM DTM. Select filters from the sidebar to customize the display. You can download data as CSV."),
    p("For more information, visit", HTML("<a href='https://dtm.iom.int/'>DTM</a>.")),
    p(HTML("For queries, please contact us at <a href='https://dtm.iom.int/contact'>here</a>.")),
    dateRangeInput('date_range', HTML("<strong style='color:#0834a4;'>Date Range</strong>"), start = Sys.Date() - 30, end = Sys.Date(), format = "yyyy-mm-dd"),
    pickerInput('country_filter', label = "Select/deselect all options", choices = NULL, selected = NULL, multiple = TRUE, options = list(`actions-box` = TRUE)),
    downloadButton('download_data', 'Download filtered data as Excel'),
    actionButton("reload_data", "Reload Data")  # Add action button for reloading data
  ),
  mainPanel(
    tabsetPanel(
      tabPanel("Summary",
               uiOutput('summary'),
               uiOutput('report_list')
      ),
      tabPanel("Data Table",
               dataTableOutput('data_table')
      )
    )
  )
)

# Server
server <- function(input, output, session) {
  # Reactive value to hold data
  df <- reactiveVal()
  
  # Function to load data with caching
  load_data <- function() {
    if (is.null(cached_data)) {
      # If no cached data, scrape data and cache it
      data <- scrape_data(pages = 10)
      cached_data <<- data
    }
    return(cached_data)
  }
  
  # Load data initially
  df(load_data())
  
  # Update country filter choices
  observe({
    updatePickerInput(session, 'country_filter', choices = unique(df()$Country_Name), selected = unique(df()$Country_Name))
  })
  
  # Filter data based on input
  filtered_data <- reactive({
    req(input$date_range)
    req(input$country_filter)
    
    df() %>%
      filter(Published_Date >= input$date_range[1] & Published_Date <= input$date_range[2]) %>%
      filter(Country_Name %in% input$country_filter)
  })
  
  # Summary data
  output$summary <- renderUI({
    total_reports <- nrow(df())
    date_range <- range(df()$Published_Date, na.rm = TRUE)
    last_48_hours_count <- df() %>% filter(Published_Date >= Sys.Date() - 2) %>% nrow()
    filtered_reports_count <- filtered_data() %>% nrow()
    
    tagList(
      h1(HTML(paste("<strong style='color:#0834a4;'>DTM Report Dashboard</strong>"))),
      p(HTML(paste("<strong>Reports updated as of:</strong>", Sys.Date()))),
      p(HTML(paste("<strong>Crawled Reports Date Range:</strong>", format(date_range[1], "%Y-%m-%d"), "-", format(date_range[2], "%Y-%m-%d")))),
      p(HTML(paste("<strong>Reports in the last 48 hours:</strong>", last_48_hours_count, "Reports", "<strong style='margin: 0 10px;'>|</strong>", "<strong>Filtered Reports Count:</strong>", filtered_reports_count))),
      hr(class = "custom-hr")
    )
  })
  
  # Render list of reports
  output$report_list <- renderUI({
    data <- filtered_data()
    reports <- lapply(1:nrow(data), function(i) {
      report <- data[i, ]
      tagList(
        h3(report$Title),
        p(paste(report$Summary)),
        p(paste(report$Published_Date, "|", report$Country_Name, "|", report$Report_Type)),
        a("Read More", href = report$Link, target = "_blank"),
        hr(class = "custom-hr_v2")
      )
    })
    do.call(tagList, reports)
  })
  
  # Render data table
  output$data_table <- renderDataTable({
    datatable(filtered_data())
  })
  
  # Download handler
  output$download_data <- downloadHandler(
    filename = function() {
      paste0("DTM_Reports_", input$date_range[1], "_to_", input$date_range[2], ".xlsx")
    },
    content = function(file) {
      writexl::write_xlsx(filtered_data(), path = file)
    }
  )
  
  # Reload data when button is clicked
  observeEvent(input$reload_data, {
    new_data <- scrape_data(pages = 10)
    cached_data <<- new_data  # Update the cache
    df(new_data)  # Update the reactive value
  })
}

# Run the application 
shinyApp(ui = ui, server = server)
