# Stage 1: Prune monorepo
FROM node:20-alpine AS pruner
RUN apk add --no-cache libc6-compat
WORKDIR /app
RUN npm install -g turbo
COPY . .
RUN turbo prune @michi/web --docker

# Stage 2: Install and Build
FROM node:20-alpine AS installer
RUN apk add --no-cache libc6-compat
WORKDIR /app

# First copy dependency files to leverage layer caching
COPY --from=pruner /app/out/json/ .
COPY --from=pruner /app/out/package-lock.json ./package-lock.json
RUN npm clean-install

# Copy project files and build
COPY --from=pruner /app/out/full/ .
COPY turbo.json turbo.json
RUN npx turbo run build --filter=@michi/web

# Stage 3: Minimal runner
FROM node:20-alpine AS runner
WORKDIR /app

# Don't run production container as root
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=installer /app/apps/web/package.json .
COPY --from=installer /app/apps/web/next.config.js .

# Standalone output folder containing minimal files
COPY --from=installer --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=installer --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=installer --chown=nextjs:nodejs /app/apps/web/public ./apps/web/public

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "apps/web/server.js"]
