import sys
import re
from pyspark.ml.recommendation import ALS
from pyspark.context import SparkContext
from pyspark.sql.session import SparkSession
from pyspark.sql import *
import math

spark = SparkSession.builder.appName("Amazon_Rec").getOrCreate()

#pre-processing
df = spark.read.json("reviews_Movies_and_TV_5.json")
df.printSchema()

df = df.select('asin','reviewerID','overall')
df.printSchema()
df.show()

#encoding ID's to fit in model
from pyspark.ml.feature import StringIndexer

a = StringIndexer(inputCol="reviewerID", outputCol="reviewerIDIndex",  handleInvalid='skip')
r = a.fit(df)
indexedDf = r.transform(df)
indexedDf.show()

asinIndexer = StringIndexer(inputCol="asin", outputCol="asinIndex",handleInvalid='skip')
a = asinIndexer.fit(df)
indexedDf = a.transform(indexedDf)
indexedDf.show()

from pyspark.sql.types import IntegerType
from pyspark.sql.functions import regexp_replace

indexedDf = indexedDf.withColumn("reviewerID", indexedDf["reviewerIDIndex"].cast(IntegerType()))
indexedDf = indexedDf.withColumn("asin",indexedDf["asinIndex"].cast(IntegerType()))
#indexedDf.show()

#indexedDf.toPandas().to_csv(indexedDf.csv, header=True, index=False)
indexedDf = indexedDf.select('asin','reviewerID','overall')

indexedDf.show()

print(indexedDf.count())

train,test=indexedDf.randomSplit([0.8,0.2])
train.show()
test.show()

als = ALS(rank=8,maxIter=4,regParam=0.04, userCol="reviewerID", itemCol="asin",ratingCol="overall", coldStartStrategy="nan")
model= als.fit(train)

from pyspark.ml.evaluation import RegressionEvaluator

predictions = model.transform(test)
predictions.show()

evaluator = RegressionEvaluator(metricName="rmse", labelCol="overall", predictionCol="prediction")
rmse = evaluator.evaluate(predictions)
#model
als = ALS(rank=8,maxIter=4,regParam=0.04, userCol="reviewerID", itemCol="asin",ratingCol="overall", coldStartStrategy="nan")
mymodel= als.fit(indexedDf)


userRecs = mymodel.recommendForAllUsers(10)

ProductRecs = mymodel.recommendForAllItems(10)


userRecs.show()
ProductRecs.show()

# Generate top 5 movie recommendations for a specified set of users
users = ratings.select(als.getUserCol()).distinct().limit(3)
userSubsetRecs = mymodel.recommendForUserSubset(users, 5)
# Generate top 5 user recommendations for a specified set of products
products = ratings.select(als.getItemCol()).distinct().limit(3)
productSubSetRecs = mymodel.recommendForItemSubset(products, 5)

userSubsetRecs.show()
ProductSubSetRecs.show()


#pred_rdd = predictions.rdd
#pred_rdd.repartition(1).saveAsTextFile("preds")


rdd1 = userRecs.rdd
rdd2 = ProductRecs.rdd

rdd1.repartition(1).saveAsTextFile("userRecs")

rdd2.repartition(1).saveAsTextFile("movieRecs")

rdd3 = userSubsetRecs.rdd
rdd4 = ProductSubsetRecs.rdd

rdd3.repartition(1).saveAsTextFile("userSubsetRecs")

rdd4.repartition(1).saveAsTextFile("movieSubsetRecs")
