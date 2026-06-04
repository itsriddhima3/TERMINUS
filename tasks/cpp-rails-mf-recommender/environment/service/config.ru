# frozen_string_literal: true

require "rack"
require_relative "config/routes"

run build_app
