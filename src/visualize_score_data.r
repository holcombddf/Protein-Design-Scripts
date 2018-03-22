#R script which produces a scatterplot from three arguments: the csv containing the relevant data, the name of the x-variable column label, and the name of the y-variable column label
options <- commandArgs(trailingOnly = TRUE)
data <- read.csv(options[1], header=TRUE, sep=",")
x <- options[2]
y <- options[3]
plot(data[[x]], data[[y]], main="Scatterplot", xlab=x, ylab=y)