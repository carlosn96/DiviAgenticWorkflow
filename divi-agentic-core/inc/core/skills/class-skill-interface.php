<?php

namespace DAC\Core\Skills;

interface Skill_Interface {
    public static function get_name(): string;
    public static function get_description(): string;
    public static function validate(array $vars): array;
    public static function get_scaffold(): array;
}
