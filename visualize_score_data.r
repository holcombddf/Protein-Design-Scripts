options <- commandArgs(trailingOnly = TRUE)
data <- read.csv(options[1], header=TRUE, sep=",")
x <- options[2]
y <- options[3]
plot(data[[x]], data[[y]], main="Scatterplot", xlab=x, ylab=y)