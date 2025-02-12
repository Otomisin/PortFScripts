library(sf)
library(dplyr)
library(gatpkg)


# Improved runGATautomated with proper exclusion handling
#' Run GAT Automation 
#'
#' @description
#' Automates running the Geographic Aggregation Tool (GAT) with specified parameters.
#' Accepts either file paths or sf objects as input.
#'
#' @param input Either a file path to a shapefile or an sf object
#' @param id_var Character, name of the unique identifier variable
#' @param boundary_var Character, name of the boundary variable (optional)
#' @param enforce_boundary Logical, whether to enforce boundary constraints
#' @param agg_var1 Character, name of first aggregation variable
#' @param min_val1 Numeric, minimum value for first aggregation variable
#' @param max_val1 Numeric, maximum value for first aggregation variable
#' @param agg_var2 Character, name of second aggregation variable (optional)
#' @param min_val2 Numeric, minimum value for second aggregation variable (optional)
#' @param max_val2 Numeric, maximum value for second aggregation variable (optional)
#' @param exclusions List of exclusion criteria, each containing:
#'   - var: variable name
#'   - operator: one of "equals", "less than", "greater than"
#'   - value: numeric threshold
#' @param merge_method Character, one of "closest", "least", "similar"
#' @param merge_params List of additional merge parameters:
#'   - centroid_type: for closest method, "geographic" or "population-weighted"
#'   - ratio_vars: for similar method, c(numerator, denominator)
#' @param pop_input Either file path to population shapefile or sf object (optional)
#' @param pop_var Character, name of population variable (optional)
#' @param calculate_rate Logical, whether to calculate rates
#' @param rate_params List of rate calculation parameters (if calculate_rate=TRUE):
#'   - name: rate variable name
#'   - numerator: numerator variable
#'   - denominator: denominator variable 
#'   - multiplier: rate multiplier
#'   - color: color scheme name
#' @param save_kml Logical, whether to save KML output
#' @param output_path Character, path to save outputs
#' @param output_name Character, base name for output files
#'
#' @return List containing:
#'   - aggregated: sf object of aggregated areas
#'   - crosswalk: sf object mapping original to aggregated areas
#'   - settings: list of GAT settings used
#'   - log: processing log messages
#'   - analysis: summary statistics and diagnostics
#'
#' @export
runGATautomated <- function(
    input,
    id_var,
    boundary_var = NULL,
    enforce_boundary = FALSE,
    agg_var1,
    min_val1,
    max_val1, 
    agg_var2 = NULL,
    min_val2 = NULL,
    max_val2 = NULL,
    exclusions = list(),
    merge_method = "closest",
    merge_params = list(),
    pop_input = NULL,
    pop_var = NULL,
    calculate_rate = FALSE,
    rate_params = list(),
    save_kml = FALSE,
    output_path,
    interactive_mode = FALSE, ## New for supressing pop up for chuncks above threshold test!!
    output_name
) {
  # Initialize settings
  mysettings <- list(
    version = utils::packageDescription("gatpkg")$Version,
    pkgdate = utils::packageDescription("gatpkg")$Date,
    adjacent = TRUE,
    pwrepeat = FALSE,
    minfirst = TRUE,
    limitdenom = FALSE,
    starttime = Sys.time(),
    quit = FALSE
  )
  
  # Process input data
  message("Processing input data...")
  area <- if(inherits(input, "sf")) {
    input 
  } else if(is.character(input)) {
    sf::st_read(input, quiet = TRUE)
  } else {
    stop("Input must be an sf object or path to shapefile")
  }
  
  validateGATInputs(area, id_var, agg_var1, min_val1, max_val1)
  
  # Process exclusions and initialize flags
  processed <- processAndApplyExclusions(area, exclusions)
  area <- processed$area
  exclist <- processed$exclist
  
  # Add required ID column
  area$GATid <- data.frame(area)[, id_var]
  
  # Setup file variables 
  filevars <- if(is.character(input)) {
    list(
      userin = input,
      filein = tools::file_path_sans_ext(basename(input)),
      pathin = dirname(input),
      userout = file.path(output_path, output_name),
      fileout = output_name,
      pathout = output_path
    )
  } else {
    list(
      userin = "",
      filein = output_name,
      pathin = output_path,
      userout = file.path(output_path, output_name),
      fileout = output_name, 
      pathout = output_path
    )
  }
  
  # Setup GAT variables
  gatvars <- list(
    myidvar = id_var,
    aggregator1 = agg_var1,
    aggregator2 = ifelse(!is.null(agg_var2), agg_var2, agg_var1),
    minvalue1 = as.character(min_val1),
    minvalue2 = ifelse(!is.null(min_val2), as.character(min_val2), as.character(min_val1)),
    maxvalue1 = as.character(max_val1),
    maxvalue2 = ifelse(!is.null(max_val2), as.character(max_val2), as.character(max_val1)),
    boundary = ifelse(!is.null(boundary_var), boundary_var, "NONE"),
    rigidbound = enforce_boundary,
    popwt = !is.null(pop_input),
    popvar = pop_var,
    savekml = save_kml,
    numrow = nrow(area),
    invalid = 0,
    exclmaxval = sum(area$GATflag == 5)
  )
  
  # Setup merge variables
  mergevars <- list(
    mergeopt1 = merge_method,
    mergeopt2 = merge_method,
    centroid = ifelse(merge_method == "closest" && !is.null(merge_params$centroid_type),
                      merge_params$centroid_type, "geographic"),
    similar1 = ifelse(merge_method == "similar" && !is.null(merge_params$ratio_vars),
                      merge_params$ratio_vars[1], "NONE"),
    similar2 = ifelse(merge_method == "similar" && !is.null(merge_params$ratio_vars),
                      merge_params$ratio_vars[2], "NONE")
  )
  
  # Setup rate variables
  ratevars <- if (!calculate_rate) {
    list(ratename = "no_rate")
  } else {
    list(
      ratename = rate_params$name,
      numerator = rate_params$numerator,
      denominator = rate_params$denominator,
      multiplier = rate_params$multiplier,
      colorname = rate_params$color,
      colorscheme = rate_params$color
    )
  }
  
  # Process population data if needed
  pop <- NULL
  if (!is.null(pop_input)) {
    message("Processing population data...")
    pop <- if(inherits(pop_input, "sf")) {
      pop_input
    } else if(is.character(pop_input)) {
      sf::st_read(pop_input, quiet = TRUE)
    } else {
      stop("pop_input must be an sf object or path to shapefile")
    }
    
    if (!is.null(pop_var)) {
      if(!pop_var %in% names(pop)) {
        stop(sprintf("Population variable '%s' not found in population data", pop_var))
      }
      pop <- pop[, pop_var]
    }
  }
  
  # Prepare for aggregation
  area_sf <- sf::st_as_sf(area)
  sf::st_agr(area_sf) <- "constant"
  
  # Run aggregation
  message("Starting aggregation process...")
  # aggvars <- defineGATmerge(
  #   area = area_sf,
  #   gatvars = gatvars,
  #   mergevars = mergevars,
  #   pop = pop,
  #   exclist = exclist,
  #   progressbar = FALSE,
  #   adjacent = TRUE,
  #   minfirst = TRUE
  # )
  
  defineGATmerge <- function(area, gatvars, mergevars, exclist = NULL,
                             pwrepeat = FALSE, adjacent = TRUE, pop = NULL,
                             minfirst = FALSE, progressbar = TRUE,
                             interactive_mode = FALSE) {
    
    # Convert popup message to console message
    if (nrow(temp$aggdata) == 0) {
      if (gatvars$aggregator1 == gatvars$aggregator2) {
        vars <- gatvars$aggregator1
      } else {
        vars <- paste(gatvars$aggregator1, "and", gatvars$aggregator2)
      }
      
      msg <- paste("All areas have values of", vars,
                   "over your selected minimum value(s). No areas were merged.")
      
      if (interactive_mode) {
        tcltk::tkmessageBox(title = "Merge failed", message = msg,
                            type = "ok", icon = "info")
      } else {
        message(msg)
      }
    }
  }

  
  message("Creating aggregated shapefile...")
  aggregated <- mergeGATareas(
    ratevars = ratevars,
    aggvars = aggvars,
    idvar = "GATid",
    myshp = area_sf
  )
  
  message("Calculating compactness ratio...")
  aggregated$GATcratio <- calculateGATcompactness(aggregated)
  
  # Generate maps
  message("Generating maps...")
  maps <- generateGATMaps(area_sf, aggregated, gatvars, mergevars, ratevars)
  
  # Save outputs
  message("Saving outputs...")
  saveGATOutputs(
    aggregated = aggregated,
    area = area_sf,
    idlist = aggvars$IDlist,
    maps = maps,
    output_path = output_path,
    output_name = output_name,
    save_kml = save_kml,
    gatvars = gatvars,
    ratevars = ratevars,
    mergevars = mergevars,
    exclist = exclist,
    mysettings = mysettings
  )
  
  # Generate analysis report
  message("Generating analysis report...")
  analysis_report <- generateGATAnalysis(
    original = area_sf,
    aggregated = aggregated,
    settings = list(
      gatvars = gatvars,
      mergevars = mergevars,
      ratevars = ratevars,
      exclist = exclist
    ),
    min_pop = min_val1,
    max_pop = max_val1
  )
  
  message(sprintf("Aggregation complete. Reduced from %d to %d areas.", 
                  nrow(area_sf), nrow(aggregated)))
  
  return(list(
    aggregated = aggregated,
    crosswalk = cbind(area_sf, GATid = aggvars$IDlist),
    settings = list(
      gatvars = gatvars,
      mergevars = mergevars,
      ratevars = ratevars,
      exclist = exclist
    ),
    log = aggvars$logmsg,
    analysis = analysis_report,
    maps = maps
  ))
}

# Helper function to validate inputs
validateGATInputs <- function(area, id_var, agg_var1, min_val1, max_val1) {
  if (!id_var %in% names(area)) {
    stop("ID variable '", id_var, "' not found in shapefile")
  }
  if (!agg_var1 %in% names(area)) {
    stop("Aggregation variable '", agg_var1, "' not found in shapefile")
  }
  if (!is.numeric(min_val1) || !is.numeric(max_val1)) {
    stop("Min and max values must be numeric")
  }
  if (min_val1 >= max_val1) {
    stop("Min value must be less than max value")
  }
  if (!inherits(area, "sf")) {
    stop("Input must be an sf object")
  }
}


processAndApplyExclusions <- function(area, exclusions) {
  # Initialize flag column if it doesn't exist
  if(!"GATflag" %in% names(area)) {
    area$GATflag <- 0
  }
  
  # If no exclusions, return unmodified data
  if(length(exclusions) == 0) {
    return(list(
      area = area,
      exclist = list(
        var1 = "NONE", var2 = "NONE", var3 = "NONE",
        math1 = "equals", math2 = "equals", math3 = "equals",
        val1 = 0, val2 = 0, val3 = 0,
        flagsum = 0
      )
    ))
  }
  
  # Initialize exclist
  exclist <- list(
    var1 = "NONE", var2 = "NONE", var3 = "NONE",
    math1 = "equals", math2 = "equals", math3 = "equals",
    val1 = 0, val2 = 0, val3 = 0
  )
  
  # Process each exclusion criterion
  for(i in seq_along(exclusions)) {
    if(i > 3) break  # GAT only handles up to 3 exclusions
    
    exc <- exclusions[[i]]
    var_name <- paste0("var", i)
    math_name <- paste0("math", i)
    val_name <- paste0("val", i)
    
    # Validate exclusion variables exist
    if(!exc$var %in% names(area)) {
      warning(sprintf("Exclusion variable '%s' not found in data", exc$var))
      next
    }
    
    # Store exclusion criteria
    exclist[[var_name]] <- exc$var
    exclist[[math_name]] <- exc$operator
    exclist[[val_name]] <- exc$value
    
    # Apply exclusion flag based on operator
    area$GATflag <- ifelse(
      area$GATflag == 0,  # Only modify unflagged areas
      case_when(
        exc$operator == "equals" ~ 
          ifelse(data.frame(area)[, exc$var] == exc$value, 1, 0),
        exc$operator == "less than" ~ 
          ifelse(data.frame(area)[, exc$var] < exc$value, 1, 0),
        exc$operator == "greater than" ~ 
          ifelse(data.frame(area)[, exc$var] > exc$value, 1, 0),
        TRUE ~ 0
      ),
      area$GATflag
    )
  }
  
  # Calculate total number of excluded areas
  exclist$flagsum <- sum(area$GATflag == 1)
  
  return(list(
    area = area,
    exclist = exclist
  ))
}

# generateGATMaps <- function(area, aggregated, gatvars, mergevars, ratevars) {
#   maps <- list()
# 
#   # Map first aggregation variable
#   temp <- defineGATmapclasses(area, aggregated, gatvars$aggregator1)
#   maps$agg1_before <- plotGATmaps(
#     area = area,
#     var = gatvars$aggregator1,
#     title.main = paste(gatvars$aggregator1, "Before Merging"),
#     colcode = temp$colcode1before,
#     mapstats = TRUE,
#     closemap = TRUE
#   )
#   maps$agg1_after <- plotGATmaps(
#     area = aggregated,
#     var = gatvars$aggregator1,
#     title.main = paste(gatvars$aggregator1, "After Merging"),
#     colcode = temp$colcode1after,
#     mapstats = TRUE,
#     closemap = TRUE
#   )
# 
#   # Map comparison
#   maps$comparison <- plotGATcompare(
#     areaold = area,
#     areanew = aggregated,
#     mergevars = mergevars,
#     gatvars = gatvars,
#     closemap = TRUE
#   )
# 
#   # Map compactness
#   maps$compactness <- plotGATmaps(
#     area = aggregated,
#     var = "GATcratio",
#     clr = "YlOrBr",
#     title.main = "Compactness Ratio After Merging",
#     ratemap = TRUE,
#     closemap = TRUE
#   )
# 
#   # Map rate if calculated
#   if (ratevars$ratename != "no_rate") {
#     maps$rate <- plotGATmaps(
#       area = aggregated,
#       var = ratevars$ratename,
#       clr = ratevars$colorscheme,
#       title.main = paste(ratevars$ratename, "After Merging"),
#       ratemap = TRUE,
#       closemap = TRUE
#     )
#   }

#   return(maps)
# }


library(ggplot2)
library(sf)

# generateGATMaps <- function(area, aggregated, gatvars, mergevars, ratevars) {
#   maps <- list()
#   
#   # Ensure data is in sf format
#   area <- st_as_sf(area)
#   aggregated <- st_as_sf(aggregated)
#   
#   # Map first aggregation variable
#   maps$agg1_before <- ggplot(area) +
#     geom_sf(aes(fill = get(gatvars$aggregator1))) +
#     scale_fill_viridis_c() +
#     ggtitle(paste(gatvars$aggregator1, "Before Merging")) +
#     theme_minimal()
#   
#   maps$agg1_after <- ggplot(aggregated) +
#     geom_sf(aes(fill = get(gatvars$aggregator1))) +
#     scale_fill_viridis_c() +
#     ggtitle(paste(gatvars$aggregator1, "After Merging")) +
#     theme_minimal()
#   
#   # Map compactness
#   if ("GATcratio" %in% colnames(aggregated)) {
#     maps$compactness <- ggplot(aggregated) +
#       geom_sf(aes(fill = GATcratio)) +
#       scale_fill_viridis_c(option = "YlOrBr") +
#       ggtitle("Compactness Ratio After Merging") +
#       theme_minimal()
#   }
#   
#   # Map rate if calculated
#   if (ratevars$ratename != "no_rate" && ratevars$ratename %in% colnames(aggregated)) {
#     maps$rate <- ggplot(aggregated) +
#       geom_sf(aes(fill = get(ratevars$ratename))) +
#       scale_fill_viridis_c(option = ratevars$colorscheme) +
#       ggtitle(paste(ratevars$ratename, "After Merging")) +
#       theme_minimal()
#   }
#   
#   return(maps)
# }

generateGATMaps <- function(area, aggregated, gatvars, mergevars, ratevars) {
  library(ggplot2)
  library(patchwork)
  library(sf)
  
  maps <- list()
  
  # Ensure data is in sf format
  area <- st_as_sf(area)
  aggregated <- st_as_sf(aggregated)
  
  # Calculate centroids for labels
  area_centroids <- st_centroid(area)
  aggregated_centroids <- st_centroid(aggregated)
  
  # Map first aggregation variable (before and after side by side)
  map_before <- ggplot(area) +
    geom_sf(aes(fill = get(gatvars$aggregator1))) +
    geom_text(data = area_centroids, 
              aes(geometry = geometry, label = get(gatvars$aggregator1)), 
              stat = "sf_coordinates", size = 3, color = "black") +
    scale_fill_viridis_c(direction = -1) +
    ggtitle(paste(gatvars$aggregator1, "Before Merging")) +
    theme_minimal() +
    theme(
      legend.position = "bottom", 
      legend.title = element_text(hjust = 0.5),
      axis.title = element_blank(),
      axis.text = element_blank(),
      axis.ticks = element_blank()
    ) +
    labs(fill = paste(gatvars$aggregator1, "Distribution"))
  
  map_after <- ggplot(aggregated) +
    geom_sf(aes(fill = get(gatvars$aggregator1))) +
    geom_text(data = aggregated_centroids, 
              aes(geometry = geometry, label = get(gatvars$aggregator1)), 
              stat = "sf_coordinates", size = 3, color = "black") +
    scale_fill_viridis_c(direction = -1) +
    ggtitle(paste(gatvars$aggregator1, "After Merging")) +
    theme_minimal() +
    theme(
      legend.position = "bottom", 
      legend.title = element_text(hjust = 0.5),
      axis.title = element_blank(),
      axis.text = element_blank(),
      axis.ticks = element_blank()
    ) +
    labs(fill = paste(gatvars$aggregator1, "Distribution"))
  
  maps$agg1_comparison <- map_before | map_after
  
  # Map compactness (if available)
  if ("GATcratio" %in% colnames(aggregated)) {
    maps$compactness <- ggplot(aggregated) +
      geom_sf(aes(fill = GATcratio)) +
      scale_fill_viridis_c(option = "YlOrBr", direction = -1) +
      ggtitle("Compactness Ratio After Merging") +
      theme_minimal() +
      theme(
        legend.position = "bottom", 
        legend.title = element_text(hjust = 0.5),
        axis.title = element_blank(),
        axis.text = element_blank(),
        axis.ticks = element_blank()
      ) +
      labs(fill = "Compactness Ratio Distribution")
  }
  
  # Map rate if calculated (before and after side by side, if applicable)
  if (ratevars$ratename != "no_rate" && ratevars$ratename %in% colnames(aggregated)) {
    map_rate_after <- ggplot(aggregated) +
      geom_sf(aes(fill = get(ratevars$ratename))) +
      geom_text(data = aggregated_centroids, 
                aes(geometry = geometry, label = get(ratevars$ratename)), 
                stat = "sf_coordinates", size = 3, color = "black") +
      scale_fill_viridis_c(option = ratevars$colorscheme, direction = -1) +
      ggtitle(paste(ratevars$ratename, "After Merging")) +
      theme_minimal() +
      theme(
        legend.position = "bottom", 
        legend.title = element_text(hjust = 0.5),
        axis.title = element_blank(),
        axis.text = element_blank(),
        axis.ticks = element_blank()
      ) +
      labs(fill = paste(ratevars$ratename, "Distribution"))
    
    map_rate_before <- ggplot(area) +
      geom_sf(aes(fill = get(ratevars$ratename))) +
      geom_text(data = area_centroids, 
                aes(geometry = geometry, label = get(ratevars$ratename)), 
                stat = "sf_coordinates", size = 3, color = "black") +
      scale_fill_viridis_c(option = ratevars$colorscheme, direction = -1) +
      ggtitle(paste(ratevars$ratename, "Before Merging")) +
      theme_minimal() +
      theme(
        legend.position = "bottom", 
        legend.title = element_text(hjust = 0.5),
        axis.title = element_blank(),
        axis.text = element_blank(),
        axis.ticks = element_blank()
      ) +
      labs(fill = paste(ratevars$ratename, "Distribution"))
    
    maps$rate_comparison <- map_rate_before | map_rate_after
  }
  
  return(maps)
}






# Improved save function to handle directory creation and large numbers
saveGATOutputs <- function(
    aggregated,
    area,
    idlist,
    maps,
    output_path,
    output_name,
    save_kml,
    gatvars,
    ratevars,
    mergevars,
    exclist,
    mysettings
) {
  # Create output directory if it doesn't exist
  dir.create(output_path, showWarnings = FALSE, recursive = TRUE)
  
  # Scale down large numeric fields
  numeric_cols <- sapply(aggregated, is.numeric)
  for(col in names(aggregated)[numeric_cols]) {
    if(max(abs(aggregated[[col]]), na.rm = TRUE) > 1e7) {
      aggregated[[col]] <- aggregated[[col]] / 1000
    }
  }
  
  numeric_cols <- sapply(area, is.numeric)
  for(col in names(area)[numeric_cols]) {
    if(max(abs(area[[col]]), na.rm = TRUE) > 1e7) {
      area[[col]] <- area[[col]] / 1000
    }
  }
  
  # Save shapefiles
  tryCatch({
    sf::st_write(
      aggregated,
      paste0(output_path, "/", output_name, ".shp"),
      delete_dsn = TRUE,
      quiet = TRUE
    )
    
    crosswalk <- cbind(area, GATid = idlist)
    sf::st_write(
      crosswalk,
      paste0(output_path, "/", output_name, "_in.shp"),
      delete_dsn = TRUE,
      quiet = TRUE
    )
  }, error = function(e) {
    warning("Error saving shapefiles: ", e$message)
  })
  
  # Save maps to PDF
  tryCatch({
    grDevices::pdf(paste0(output_path, "/", output_name, "_plots.pdf"))
    for (map in maps) {
      if (is(map, "recordedplot")) grDevices::replayPlot(map)
    }
    grDevices::dev.off()
  }, error = function(e) {
    warning("Error saving plots: ", e$message)
  })
  
  # Save KML if requested
  if (save_kml) {
    tryCatch({
      writeGATkml(
        myshp = aggregated,
        filename = output_name,
        filepath = output_path,
        myidvar = gatvars$myidvar
      )
    }, error = function(e) {
      warning("Error saving KML: ", e$message)
    })
  }
  
  # Save settings
  tryCatch({
    save(
      gatvars, mergevars, ratevars, exclist, mysettings,
      file = paste0(output_path, "/", output_name, "_settings.Rdata")
    )
  }, error = function(e) {
    warning("Error saving settings: ", e$message)
  })
}


## Report Generator  -----------------

generateGATAnalysis <- function(original, aggregated, settings, min_pop, max_pop) {
  library(data.table)
  
  # Calculate key metrics
  orig_areas <- nrow(original)
  agg_areas <- nrow(aggregated)
  reduction <- round((orig_areas - agg_areas) / orig_areas * 100, 1)
  
  # Population distribution before
  orig_pop <- data.frame(original)[, settings$gatvars$aggregator1]
  orig_stats <- summary(orig_pop)
  
  # Population distribution after
  agg_pop <- data.frame(aggregated)[, settings$gatvars$aggregator1]
  agg_stats <- summary(agg_pop)
  
  # Calculate areas outside bounds
  orig_below_min <- sum(orig_pop < min_pop)
  orig_above_max <- sum(orig_pop > max_pop)
  agg_below_min <- sum(agg_pop < min_pop)
  agg_above_max <- sum(agg_pop > max_pop)
  
  # Safely handle compactness statistics
  getCompactnessStats <- function(data) {
    # Check if GATcratio exists and is numeric
    if ("GATcratio" %in% names(data)) {
      ratios <- as.numeric(data$GATcratio)
      if (!all(is.na(ratios))) {
        stats <- summary(ratios)
        mean_val <- mean(ratios, na.rm = TRUE)
        return(c(
          min(ratios, na.rm = TRUE),
          stats["Median"],
          mean_val,
          max(ratios, na.rm = TRUE)
        ))
      }
    }
    return(rep(NA, 4))
  }
  
  # Get compactness statistics
  orig_compact_stats <- getCompactnessStats(original)
  agg_compact_stats <- getCompactnessStats(aggregated)
  
  # Create data tables for each section
  area_stats <- data.table(
    Metric = c("Number of Areas", "Reduction Percentage",
               "Areas Below Min Pop", "Areas Above Max Pop"),
    Before = c(orig_areas, "-", 
               orig_below_min, orig_above_max),
    After = c(agg_areas, paste0(reduction, "%"),
              agg_below_min, agg_above_max)
  )
  
  pop_stats <- data.table(
    Metric = c("Minimum Population", "Median Population", 
               "Mean Population", "Maximum Population"),
    Before = round(c(orig_stats["Min."], orig_stats["Median"], 
                     mean(orig_pop), orig_stats["Max."]), 1),
    After = round(c(agg_stats["Min."], agg_stats["Median"], 
                    mean(agg_pop), agg_stats["Max."]), 1)
  )
  
  # Create data tables for each section
  compact_stats_dt <- data.table(
    Metric = c("Minimum Ratio", "Median Ratio", 
               "Mean Ratio", "Maximum Ratio"),
    Before = round(orig_compact_stats, 3),
    After = round(agg_compact_stats, 3)
  )
  
  # Format output
  cat("\nGAT ANALYSIS REPORT>>>>>>>>>>>>>>>>>>>>\n")
  cat("\n----------------------------------------------------\n")
  
  cat("\nAREA STATISTICS\n")
  cat("\n----------------------------------------------------\n")
  print(area_stats, row.names = FALSE)
  
  cat("\nPOPULATION STATISTICS\n")
  cat("\n----------------------------------------------------\n")
  cat(sprintf("\nTarget Range: %d - %d\n", min_pop, max_pop))
  print(pop_stats, row.names = FALSE)
  
  cat("\nCOMPACTNESS STATISTICS\n")
  cat("\n----------------------------------------------------\n")
  if (all(is.na(orig_compact_stats)) || all(is.na(agg_compact_stats))) {
    cat("Note: Compactness ratios could not be calculated\n")
  } else {
    print(compact_stats_dt, row.names = FALSE)
  }
  
  # Return a list of all tables for further use if needed
  return(list(
    area_stats = area_stats,
    pop_stats = pop_stats,
    compact_stats = compact_stats_dt
  ))
}


# ## Example ###############
# 
# timestamp <- format(Sys.time(), "%Y%m%d_%H%M%S")
# output_dir <- file.path("C:/Users/orenaike/OneDrive/02_JOBS/IOM/1_OPERATIONS/auto_deliniation_script/gatpkg/inst/testresult",
#                         paste0(timestamp, "_GAT"))
# 
# result_no_exclusions <- runGATautomated(
#   input = "C:/Users/orenaike/OneDrive/02_JOBS/IOM/1_OPERATIONS/auto_deliniation_script/gatpkg/inst/extdata/hftown.shp", # Changed from shp_path to input
#   id_var = "ID",
#   boundary_var = "COUNTY",
#   enforce_boundary = TRUE,
#   agg_var1 = "TOTAL_POP",
#   min_val1 = 6000,
#   max_val1 = 15000,
#   merge_method = "closest",
#   merge_params = list(centroid_type = "geographic"),
#   output_path = output_dir,
#   output_name = "aggregated_with_exclusions"
# )
# 
# 
# 
# print(result_no_exclusions$aggregated)
# 
# print(result_no_exclusions$crosswalk)
# 
# # View analysis report
# print(result_no_exclusions$analysis)