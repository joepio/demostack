# MijnOverheid-demo uit het VNG API Lab, met een adapter die zaken en taken uit de echte registers haalt.
# De app zelf blijft ongewijzigd, op een paar regels na: de standaard-API-basis wordt de eigen origin
# (in plaats van de mockserver), zodat de adapter bepaalt welke API's echt zijn en welke mock blijven,
# de naam van de ingelogde inwoner vervangt de demopersona en Uitloggen logt echt uit.
FROM node:22-alpine AS build
ARG LAB_COMMIT=482be6e63b410fbf0b9d4a88a98e069e28adc7bf
RUN apk add --no-cache git && corepack enable
WORKDIR /src
RUN git clone https://github.com/VNG-Realisatie/VNG-API-Lab.git . && git checkout "$LAB_COMMIT"
WORKDIR /src/mijnoverheid
RUN sed -i 's|    : "https://vng-interactie-mocks.fly.dev";|    : window.location.origin;|' src/App.tsx \
 && sed -i -e 's|<h1>Hallo Jeroen van Drouwen</h1>|<h1>Hallo {(window as any).__MO_NAAM__ \|\| "Jeroen van Drouwen"}</h1>|' \
          -e 's|<span>Jeroen van Drouwen</span>|<span>{(window as any).__MO_NAAM__ \|\| "Jeroen van Drouwen"}</span>|' \
          -e 's|^\( *\)Jeroen van Drouwen$|\1{(window as any).__MO_NAAM__ \|\| "Jeroen van Drouwen"}|' \
          -e 's|<a href="/">Uitloggen</a>|<a href="/logout">Uitloggen</a>|' src/App.tsx \
 && grep -q 'window.location.origin;' src/App.tsx && test "$(grep -c '__MO_NAAM__' src/App.tsx)" = 3 \
 && pnpm install --frozen-lockfile=false && pnpm exec vite build

FROM python:3.13-alpine
RUN pip install --no-cache-dir requests==2.32.5 "pyjwt[crypto]==2.10.1"
COPY --from=build /src/mijnoverheid/dist /app/static
COPY app.py /app/app.py
USER 1000
EXPOSE 8080
CMD ["python", "/app/app.py"]
