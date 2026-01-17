FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /app
COPY . .
RUN dotnet publish src/F1LapAnalyzer.Api -c Release -o out

FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY --from=build /app/out .
ENV ASPNETCORE_URLS=http://+:10000
ENV ML_SERVICE_URL=https://f1-ml-service-zsno.onrender.com
EXPOSE 10000
ENTRYPOINT ["dotnet", "F1LapAnalyzer.Api.dll"]
