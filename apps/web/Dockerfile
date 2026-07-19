# syntax=docker/dockerfile:1
FROM node:20-slim AS base
ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH
RUN corepack enable

FROM base AS build
WORKDIR /app
# Copy workspace manifests for install caching
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/web/package.json apps/web/package.json
COPY packages/shared-types/package.json packages/shared-types/package.json
RUN pnpm install --frozen-lockfile || pnpm install
COPY . .
RUN pnpm --filter web build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
# Next standalone output: a self-contained server + minimal node_modules (no pnpm at runtime).
# With outputFileTracingRoot at the monorepo root, the bundle nests under apps/web.
COPY --from=build /app/apps/web/.next/standalone ./
COPY --from=build /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=build /app/apps/web/public ./apps/web/public
# server.js reads $PORT (Cloud Run injects it; defaults to 3000 locally/compose).
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
